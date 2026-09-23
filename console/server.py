"""Loopback-only policy editor. No model calls, shell execution, or remote API."""
from __future__ import annotations
import argparse
import copy
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
import tempfile
import threading
from urllib.parse import urlparse
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
STATIC = Path(__file__).resolve().parent / 'web'
spec = importlib.util.spec_from_file_location('router_engine', ROOT / 'workspace-router/scripts/router.py')
router = importlib.util.module_from_spec(spec)
spec.loader.exec_module(router)
TRIGGERS = ['explicit_user', 'verification_gap', 'deadline_parallel']
MODEL_DEFAULTS = ['gpt-6-luna', 'gpt-6-sol', 'gpt-6-astra', 'gpt-5.6-sol', 'gpt-5.6-terra']

class Conflict(Exception):
    pass

def revision(raw):
    return hashlib.sha256(raw).hexdigest()

def validate(policy):
    policy = copy.deepcopy(policy)
    router.validate_policy(policy)
    allowed = {'schema_version', 'version', 'enabled', 'preference', 'delegation_mode',
               'max_children', 'max_children_per_request', 'max_recovery_attempts',
               'minimum_reasoning_minutes', 'catalog_max_age_hours', 'triggers', 'lanes', 'classification_mode', 'routing_strategy'}
    if set(policy) - allowed:
        raise ValueError('Unknown policy fields')
    if not 1 <= policy['max_children'] <= policy['max_children_per_request'] <= 3:
        raise ValueError('并发数必须在 1–3 之间，且不超过累计启动上限。')
    if not 0 <= policy['minimum_reasoning_minutes'] <= 60:
        raise ValueError('工作量门槛需要在 0–60 分钟之间。')
    if not .25 <= policy['catalog_max_age_hours'] <= 24:
        raise ValueError('能力记录有效期需要在 0.25–24 小时之间。')
    if not re.fullmatch(r'[A-Za-z0-9.+_-]{1,40}', policy['version']):
        raise ValueError('策略版本格式无效。')
    for lane, pairs in policy['lanes'].items():
        if lane not in router.LANES or not 1 <= len(pairs) <= 4:
            raise ValueError('每个分档需要 1–4 个候选模型。')
        seen = set()
        for model, effort in pairs:
            if not re.fullmatch(r'[A-Za-z0-9_.:/-]{1,100}', model):
                raise ValueError('模型 ID 只能包含字母、数字及 . _ : / -。')
            if (model, effort) in seen:
                raise ValueError('同一分档中不能重复添加相同模型与强度。')
            seen.add((model, effort))
    return policy


class PolicyStore:
    def __init__(self, path, data_dir):
        self.path = Path(path).resolve(strict=True)
        self.data_dir = Path(data_dir).resolve()
        self.history_dir = self.data_dir / 'history'
        self.lock = threading.RLock()
        validate(json.loads(self.path.read_text(encoding='utf-8-sig')))

    def state(self):
        raw = self.path.read_bytes()
        policy = validate(json.loads(raw.decode('utf-8-sig')))
        return {'policy': policy, 'revision': revision(raw), 'target': str(self.path),
                'engine_version': router.VERSION, 'models': MODEL_DEFAULTS,
                'recommended_policy': validate(router.read_json(router.RECOMMENDED_POLICY)),
                'presets': {key: validate(value) for key, value in router.read_json(router.PRESETS).items()},
                'capabilities_live': False, 'history': self.history()}

    def history(self):
        rows = []
        if self.history_dir.exists():
            for p in sorted(self.history_dir.glob('*.json'), reverse=True)[:30]:
                try:
                    data = json.loads(p.read_text(encoding='utf-8'))
                    if data.get('target') != str(self.path):
                        continue
                    rows.append({'id': p.stem, 'created_at': data['created_at'],
                                 'revision': data['revision'], 'policy': data['policy']})
                except (ValueError, KeyError, OSError):
                    continue
        return rows

    def save(self, policy, expected):
        candidate = validate(policy)
        with self.lock:
            raw = self.path.read_bytes()
            if not isinstance(expected, str) or not secrets.compare_digest(revision(raw), expected):
                raise Conflict('文件已被其他程序修改。请重新载入后再应用，避免覆盖更新。')
            old_policy = json.loads(raw.decode('utf-8-sig'))
            if old_policy == candidate:
                return {**self.state(), 'unchanged': True}
            now = datetime.now(timezone.utc)
            self.history_dir.mkdir(parents=True, exist_ok=True)
            record = {'created_at': now.isoformat(), 'revision': revision(raw),
                      'target': str(self.path), 'policy': old_policy}
            name = now.strftime('%Y%m%dT%H%M%S%f') + '-' + secrets.token_hex(4)
            backup = self.history_dir / (name + '.json')
            with backup.open('x', encoding='utf-8') as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
            encoded = (json.dumps(candidate, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
            fd, temp_name = tempfile.mkstemp(prefix='.router-policy-', suffix='.tmp', dir=self.path.parent)
            temporary = Path(temp_name)
            try:
                with os.fdopen(fd, 'wb') as f:
                    f.write(encoded)
                    f.flush()
                    os.fsync(f.fileno())
                # External edits are checked again immediately before atomic replacement.
                if revision(self.path.read_bytes()) != expected:
                    raise Conflict('保存期间检测到外部修改，请重新载入。')
                os.replace(temporary, self.path)
            finally:
                if temporary.exists():
                    temporary.unlink()
            return {**self.state(), 'unchanged': False}


SCENARIOS = {
    'routine': ('none', 'edit', 'routine', 'normal', 'normal', 12, 'none'),
    'review': ('verification_gap', 'read', 'complex', 'normal', 'normal', 8, 'quality'),
    'explicit': ('explicit_user', 'read', 'routine', 'normal', 'normal', 6, 'quality'),
    'deadline': ('deadline_parallel', 'edit', 'routine', 'normal', 'normal', 10, 'parallel'),
    'critical': ('verification_gap', 'read', 'critical', 'high', 'high', 12, 'quality'),
    'tiny': ('explicit_user', 'read', 'mechanical', 'low', 'low', 1, 'quality'),
    'mechanical': ('explicit_user', 'read', 'mechanical', 'low', 'low', 8, 'quality'),
    'architecture': ('explicit_user', 'read', 'routine', 'normal', 'high', 15, 'quality'),
    'local_trial': ('explicit_user', 'edit', 'routine', 'low', 'low', 10, 'quality'),
    'borderline': ('explicit_user', 'read', 'routine', 'normal', 'normal', 10, 'quality'),
}

ASSESSMENTS = {
    'routine': ('implement', 'bounded', 'tests', 'local'),
    'review': ('review', 'bounded', 'judgment', 'cross_component'),
    'explicit': ('implement', 'bounded', 'tests', 'local'),
    'deadline': ('implement', 'bounded', 'tests', 'local'),
    'critical': ('review', 'bounded', 'judgment', 'local'),
    'tiny': ('extract', 'exact', 'deterministic', 'local'),
    'mechanical': ('extract', 'exact', 'deterministic', 'local'),
    'architecture': ('design', 'open', 'judgment', 'system'),
    'local_trial': ('implement', 'exact', 'tests', 'local'),
    'borderline': ('implement', 'bounded', 'tests', 'local'),
}

def simulate(policy, options):
    policy = validate(policy)
    scenario = options.get('scenario', 'review')
    if scenario not in SCENARIOS:
        raise ValueError('未知模拟场景。')
    basis, work, complexity, consequence, uncertainty, minutes, benefit = SCENARIOS[scenario]
    fields = ['kind', 'specification', 'verification', 'scope']
    assessment = dict(zip(fields, ASSESSMENTS[scenario]))
    assessment['evidence'] = 'Synthetic fixture with declared specification, verification, scope and risk'
    assessment.update(input_form='text', boundary='adjacent' if scenario == 'borderline' else 'clear')
    if scenario == 'borderline':
        assessment['boundary_evidence'] = 'Known local API; ownership of one adjacent state interaction is unresolved'
    if 'minutes' in options:
        minutes = router.number(options['minutes'])
        if minutes > 120:
            raise ValueError('模拟工作量超过范围。')
    active = router.count(options.get('active_children', 0))
    started = router.count(options.get('children_started', active))
    if active > 3 or started > 6 or started < active:
        raise ValueError('模拟代理计数无效。')
    environment = options.get('environment', 'ready')
    if environment not in {'ready', 'conflict', 'offline', 'no-models'}:
        raise ValueError('未知模拟环境。')
    with tempfile.TemporaryDirectory(prefix='router-simulation-') as directory:
        base = Path(directory)
        out = base / 'output'
        read = base / 'input'
        models = sorted(set(MODEL_DEFAULTS) | {m for pairs in policy['lanes'].values() for m, _ in pairs})
        q = {
            'schema_version': 1, 'depth': 0,
            'host': {'id': 'simulation', 'os': 'windows' if os.name == 'nt' else 'posix',
                     'cwd': directory, 'verified': True},
            'runtime': {'host_id': 'simulation', 'delegation_available': True, 'slots_available': 3,
                        'active_children': active, 'children_started': started},
            'scope': {'confirmed': True, 'read_roots': [directory], 'write_roots': [str(out)],
                      'protected_paths': [str(read)]},
            'delegation': {'reason': basis, 'evidence': 'Synthetic independent verification / user request',
                           'user_requested': basis == 'explicit_user', 'user_prioritized_speed': basis == 'deadline_parallel'},
            'task': {'trivial': False, 'tool_bound': False, 'independent': True, 'context_complete': True,
                     'work_type': work, 'complexity': complexity, 'consequence': consequence, 'uncertainty': uncertainty,
                     'assessment': assessment,
                     'benefit': benefit, 'reasoning_minutes': minutes, 'read_paths': [str(read)],
                     'write_paths': [str(out)] if work == 'edit' else [], 'resources': [],
                     'acceptance': ['Return reproducible evidence for the synthetic task'], 'constraints': ['Simulation only']},
            'active': [], 'failure': {'kind': 'network' if environment == 'offline' else 'none', 'recovery_attempts': 0},
            'catalog': {'host_id': 'simulation', 'source': 'runtime-tool', 'captured_at': datetime.now(timezone.utc).isoformat(),
                        'models': [{'model': m, 'efforts': router.EFFORTS[:4]} for m in models] if environment != 'no-models' else []}}
        if environment == 'conflict':
            q['active'] = [{'host_id': 'simulation', 'read_paths': [], 'write_paths': [str(read)], 'resources': []}]
        result = router.decide(q, policy)
        # Do not expose synthetic paths or a dispatch capsule; no agent is ever started.
        result.pop('spawn', None)
        return {'simulation': True, 'capabilities_live': False, 'scenario': scenario,
                'assumptions': 'Synthetic task; configured models are assumed available unless no-models is selected.',
                'result': result}


class ConsoleServer(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, port, store, token=None):
        self.store = store
        self.token = token or secrets.token_urlsafe(32)
        super().__init__(('127.0.0.1', port), Handler)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send_data(self, status, body, content_type='application/json; charset=utf-8'):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(body)

    def allowed(self, api=False):
        port = self.server.server_port
        hosts = {f'127.0.0.1:{port}', f'localhost:{port}'}
        if self.headers.get('Host') not in hosts:
            self.send_data(403, {'error': '仅允许本地访问。'})
            return False
        origin = self.headers.get('Origin')
        if origin and origin not in {f'http://{h}' for h in hosts}:
            self.send_data(403, {'error': '请求来源不被允许。'})
            return False
        if api and not secrets.compare_digest(self.headers.get('X-Router-Token', ''), self.server.token):
            self.send_data(401, {'error': '本地会话已失效，请使用启动器重新打开控制台。'})
            return False
        return True

    def do_GET(self):
        path = urlparse(self.path).path
        if not self.allowed(path.startswith('/api/')):
            return
        try:
            if path == '/api/state':
                return self.send_data(200, self.server.store.state())
            mapping = {'/': ('index.html', 'text/html; charset=utf-8'),
                       '/app.css': ('app.css', 'text/css; charset=utf-8'),
                       '/app.js': ('app.js', 'text/javascript; charset=utf-8')}
            if path in mapping:
                file, mime = mapping[path]
                return self.send_data(200, (STATIC / file).read_bytes(), mime)
            self.send_data(404, {'error': '页面不存在。'})
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self.send_data(500, {'error': '读取策略失败，请检查文件和权限。', 'type': type(exc).__name__})

    def do_POST(self):
        if not self.allowed(True):
            return
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.send_data(415, {'error': '需要 JSON 请求。'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 65536:
                return self.send_data(413, {'error': '请求大小无效。'})
            data = json.loads(self.rfile.read(length))
            path = urlparse(self.path).path
            if path == '/api/validate':
                validate(data['policy'])
                return self.send_data(200, {'valid': True})
            if path == '/api/simulate':
                return self.send_data(200, simulate(data['policy'], data.get('options', {})))
            if path == '/api/save':
                return self.send_data(200, self.server.store.save(data['policy'], data['revision']))
            self.send_data(404, {'error': '接口不存在。'})
        except Conflict as exc:
            self.send_data(409, {'error': str(exc)})
        except (ValueError, TypeError, KeyError, AttributeError, IndexError) as exc:
            self.send_data(400, {'error': str(exc) or '策略内容无效。'})
        except OSError as exc:
            self.send_data(500, {'error': '操作失败，请重新载入并检查配置及写入权限。', 'type': type(exc).__name__})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    group = p.add_mutually_exclusive_group()
    group.add_argument('--policy', type=Path, help='Edit only this fixed policy file')
    group.add_argument('--installed', action='store_true', help='Edit CODEX_HOME/skills/workspace-router policy')
    p.add_argument('--data-dir', type=Path, default=ROOT / '.local/console')
    p.add_argument('--port', type=int, default=8765)
    p.add_argument('--open', action='store_true', help='Open the local browser')
    args = p.parse_args()
    if args.installed:
        home = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex')))
        path = home / 'skills/workspace-router/references/policy.json'
        installed_router = path.parents[1] / 'scripts/router.py'
        if not installed_router.exists() or f'VERSION = "{router.VERSION}"' not in installed_router.read_text(encoding='utf-8'):
            p.error(f'Installed router must match console engine {router.VERSION} before using --installed.')
    else:
        path = args.policy or ROOT / 'workspace-router/references/policy.json'
    store = PolicyStore(path, args.data_dir)
    server = ConsoleServer(args.port, store)
    url = f'http://127.0.0.1:{server.server_port}/#token={server.token}'
    print(json.dumps({'url': url, 'policy': str(store.path), 'mode': 'local-only', 'engine': router.VERSION}), flush=True)
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == '__main__':
    main()
