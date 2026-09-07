import importlib
import io
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
verify_archive = importlib.import_module("verify-archive").verify_archive


class ReleaseSecurityTests(unittest.TestCase):
    def check_archive(self, name, data=b"safe", symlink=False):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "test.tgz"
            with tarfile.open(archive, "w:gz") as tar:
                entry = tarfile.TarInfo(name)
                if symlink:
                    entry.type = tarfile.SYMTYPE
                    entry.linkname = "../../outside"
                else:
                    entry.size = len(data)
                tar.addfile(entry, None if symlink else io.BytesIO(data))
            return verify_archive(archive, ["SKILL.md"])

    def test_allows_reviewed_file(self):
        self.assertEqual(self.check_archive("package/SKILL.md"), 1)

    def test_rejects_unexpected_private_task_spec(self):
        with self.assertRaises(ValueError):
            self.check_archive("package/.maestro/specs/private.md")

    def test_rejects_traversal_and_symlinks(self):
        for name, link in [("package/../../SKILL.md", False), ("package/SKILL.md", True)]:
            with self.subTest(name=name, link=link), self.assertRaises(ValueError):
                self.check_archive(name, symlink=link)

    def test_rejects_secret_without_echoing_it(self):
        secret = b"npm_" + b"X" * 36
        with self.assertRaises(ValueError) as error:
            self.check_archive("package/SKILL.md", secret)
        self.assertNotIn(secret.decode(), str(error.exception))

    def test_rejects_personal_absolute_path(self):
        with self.assertRaises(ValueError):
            self.check_archive("package/SKILL.md", b"C:\\Users\\privateperson\\project")
