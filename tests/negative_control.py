#!/usr/bin/env python3
"""Prove the checker can fail: the known-bad fixture must BLOCK and the clean one must PASS."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "voice_check.py"


def run(path):
    return subprocess.run([sys.executable, str(SCRIPT), str(path), "--quiet"], capture_output=True, text=True, encoding="utf-8")


bad = run(ROOT / "tests" / "fixtures" / "ai_tells.md")
good = run(ROOT / "tests" / "fixtures" / "clean.md")
ok = bad.returncode == 1 and "VOICE_CHECK_BLOCK" in bad.stdout and good.returncode == 0 and "VOICE_CHECK_PASS" in good.stdout
print("bad=%d good=%d" % (bad.returncode, good.returncode))
print("NEGATIVE_CONTROL_OK" if ok else "NEGATIVE_CONTROL_FAILED")
sys.exit(0 if ok else 1)
