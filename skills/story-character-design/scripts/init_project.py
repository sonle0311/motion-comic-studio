# -*- coding: utf-8 -*-
"""Put the drawing machine into a project.

    python3 init_project.py <project-dir>            # never overwrites an existing file
    python3 init_project.py <project-dir> --update   # refresh core.py and export.py from the skill

cast.py and the project's .md files are never overwritten.
"""
import os
import shutil
import sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE = ("core.py", "export.py")
DOCS = ("CHARACTER-DOSSIER.md", "DRAWING-RULES.md", "MISTAKES-LOG.md")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    project = os.path.abspath(args[0])
    update = "--update" in sys.argv
    dst = os.path.join(project, "drawkit")
    if not os.path.isdir(dst):
        os.makedirs(dst)
    jobs = [(os.path.join(SKILL, "scripts", "drawkit", f), os.path.join(dst, f), update) for f in ENGINE]
    jobs.append((os.path.join(SKILL, "scripts", "drawkit", "cast.py"), os.path.join(dst, "cast.py"), False))
    for f in DOCS:
        jobs.append((os.path.join(SKILL, "assets", f), os.path.join(project, f), False))
    for src, to, overwrite in jobs:
        if os.path.exists(to) and not overwrite:
            print("kept       " + to)
            continue
        if os.path.exists(to):
            shutil.copy2(to, to + ".bak")
            print("backed up  " + to + ".bak")
        shutil.copy2(src, to)
        print("copied     " + to)
    print("\nNext: fill in CHARACTER-DOSSIER.md, declare the characters in drawkit/cast.py, "
          "then run: python3 %s" % os.path.join(dst, "export.py"))


if __name__ == "__main__":
    main()
