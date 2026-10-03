#!/usr/bin/env python3
"""Create the applicant/ profile folder (story bank, facts ledger, voice, tracker).

Usage: python profile_init.py [target_dir]   (default: ./applicant)
Never overwrites existing files. Adds applicant/ to .gitignore if a .gitignore exists or a git repo is present.
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "applicant-template")


def main():
    target = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "applicant")
    os.makedirs(target, exist_ok=True)
    os.makedirs(os.path.join(target, "drafts"), exist_ok=True)
    created, kept = [], []
    for name in sorted(os.listdir(TEMPLATE)):
        dst = os.path.join(target, name)
        if os.path.exists(dst):
            kept.append(name)
        else:
            shutil.copy(os.path.join(TEMPLATE, name), dst)
            created.append(name)
    parent = os.path.dirname(target)
    gi = os.path.join(parent, ".gitignore")
    entry = os.path.basename(target) + "/"
    if os.path.exists(gi) or os.path.isdir(os.path.join(parent, ".git")):
        lines = open(gi, encoding="utf-8").read().splitlines() if os.path.exists(gi) else []
        if entry not in lines:
            with open(gi, "a", encoding="utf-8") as f:
                f.write(("\n" if lines and lines[-1] else "") + entry + "\n")
            print(f"added {entry} to {gi} (keeps your personal data out of git)")
    print(f"profile folder: {target}")
    print("created: " + (", ".join(created) or "nothing (all files already exist)"))
    if kept:
        print("kept existing: " + ", ".join(kept))


if __name__ == "__main__":
    main()
