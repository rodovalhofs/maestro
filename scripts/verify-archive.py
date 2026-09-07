"""Inspect actual npm tar bytes, without extracting or executing package contents."""
import argparse
import json
import re
import tarfile
from pathlib import Path

SECRET_PATTERNS = [
    rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    rb"\bnpm_[A-Za-z0-9]{30,}\b",
    rb"\b(?:ghp_|github_pat_|sk-proj-|xox[baprs]-)[A-Za-z0-9_-]{20,}\b",
    rb"\bAKIA[A-Z0-9]{16}\b",
    rb"(?i)[a-z]:[\\/]Users[\\/](?!Public\b|Default\b)[a-z0-9_.-]+",
    rb"/(?:home|Users)/[a-zA-Z0-9_.-]+/",
]


def verify_archive(path, expected):
    seen = set()
    with tarfile.open(path, "r:gz") as archive:
        for member in archive:
            if not member.isfile() or not member.name.startswith("package/"):
                raise ValueError(f"Unexpected archive member type/path: {member.name}")
            name = member.name.removeprefix("package/")
            if name not in expected or name in seen:
                raise ValueError(f"Unexpected or duplicate release file: {name}")
            if member.size > 1_000_000:
                raise ValueError(f"Oversized release file: {name}")
            seen.add(name)
            data = archive.extractfile(member).read()
            for pattern in SECRET_PATTERNS:
                if re.search(pattern, data):
                    # Never print the matching secret.
                    raise ValueError(f"Potential secret or personal path in release file: {name}")
    missing = set(expected) - seen
    if missing:
        raise ValueError(f"Missing release files: {sorted(missing)}")
    return len(seen)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--expected", required=True, type=Path)
    args = parser.parse_args()
    print(f"Archive inspection passed: {verify_archive(args.archive, json.loads(args.expected.read_text()))} reviewed files")
