# FAQ and troubleshooting

**English** | [简体中文](faq.zh-CN.md) · [Documentation](README.md)

## Does this switch the model for every message?

No. The current main model receives the request. The Skill can recommend a supported model for a justified child task. There is no pre-request interception layer.

## Do I have to mention the Skill each time?

Implicit invocation is permitted, so Codex may load it for matching work. That is not a guaranteed per-message trigger, and loading it does not mean a child starts. Use `$workspace-router` when you specifically want its workflow.

## Does it need API billing if I use a subscription?

The helper and console make no model API calls and require no separate router key. Actual agents run through capabilities already available in your Codex session. Availability and usage remain subject to that account and runtime. No subscription saving percentage has been measured.

## Why did Economy choose Sol or Astra?

The Luna trial needs exact requirements, meaningful tests, local text-only work, clear boundaries, low consequence and low uncertainty. Other work follows its established lane; high-consequence work keeps the critical floor. See [all conditions](../workspace-router/references/presets.md).

## The Skill does not appear

Check the execution host, the client's supported discovery directory and that the folder contains `SKILL.md`. Avoid duplicate same-name installations. Start a new task; restart the client if discovery has not refreshed. [Installation details](installation.md)

## I saved a policy but routing did not change

Check the console's **Policy source**. Plain `run_console.py` edits the repository sample; `--installed` edits the companion installer's target. Manual installations need `--policy`. Changes apply when future decisions reread the file, not to already dispatched children. SSH hosts have separate installations.

## A model is unavailable or a simulation differs from live work

Simulations use synthetic capabilities. They do not inspect your subscription or remote host. Live routing requires the current host to support the exact model and effort. An explicit unavailable choice is reported rather than silently substituted. No supported critical route means the coordinator must resolve the limitation before claiming critical acceptance.

## The console reports a version mismatch, access error or save conflict

- **Version mismatch:** upgrade the installed Skill and console from the same reviewed source; preserve private workspace notes.
- **Access error:** use the complete URL printed by the current launch, including its temporary token. Never publish that URL.
- **Save conflict:** export any draft you need, reload the current file, then reapply the intended changes.

## Do I need to keep the console running?

Only while editing or simulating policies. After saving, you can close it. The Skill reads the saved file; the console is not an always-on routing daemon.

## Can it control my browser or remote computer?

It does not add tools. Existing Codex permissions and runtime capabilities govern browser, computer and SSH work. Shared interactive actions remain with the coordinator.
