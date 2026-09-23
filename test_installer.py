import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("installer", Path(__file__).with_name("install_router.py"))
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.home = self.root / "codex"
        for relative in installer.REQUIRED:
            p = self.source / relative
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("fixture", encoding="utf-8")

    def test_preview_writes_nothing(self):
        r = installer.install(self.source, self.home)
        self.assertFalse(r["applied"])
        self.assertFalse(self.home.exists())

    def test_install_and_idempotence(self):
        self.assertTrue(installer.install(self.source, self.home, apply=True)["applied"])
        self.assertEqual(installer.install(self.source, self.home, apply=True)["action"], "unchanged")

    def test_replace_preserves_backup_and_unrelated(self):
        installer.install(self.source, self.home, apply=True)
        config = self.home / "config.toml"
        config.write_text("KEEP", encoding="utf-8")
        (self.source / "SKILL.md").write_text("changed", encoding="utf-8")
        with self.assertRaises(ValueError):
            installer.install(self.source, self.home, apply=True)
        r = installer.install(self.source, self.home, apply=True, replace=True)
        self.assertEqual((Path(r["backup"]) / "SKILL.md").read_text(), "fixture")
        self.assertEqual(config.read_text(), "KEEP")
        self.assertFalse(installer.under(Path(r["backup"]), self.home / "skills"))

    def test_incomplete_package_rejected(self):
        (self.source / "SKILL.md").unlink()
        with self.assertRaises(ValueError):
            installer.install(self.source, self.home, apply=True)
        self.assertFalse(self.home.exists())

    def test_overlapping_source_rejected(self):
        with self.assertRaises(ValueError):
            installer.install(self.source, self.source / "nested", apply=True)


if __name__ == "__main__":
    unittest.main()
