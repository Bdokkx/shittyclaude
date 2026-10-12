"""Assemble README.md: docs/readme_head.md + docs/readme_changes.md + generated tables + footer.

    python tools/make_readme.py
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable


def path(n, by_i):
    out = []
    while n is not None:
        out.append(n["name"])
        n = by_i.get(n["parent"]) if n["parent"] is not None else None
    return "/".join(reversed(out))


def main():
    head = open(os.path.join(ROOT, "docs", "readme_head.md")).read()
    changes = open(os.path.join(ROOT, "docs", "readme_changes.md")).read()
    tables = subprocess.run([PY, os.path.join(ROOT, "tools", "readme_tables.py")], capture_output=True, text=True,
                            check=True).stdout
    foot = open(os.path.join(ROOT, "docs", "readme_foot.md")).read()
    text = head + "\n![inside plan](previews/plan_inside.jpg)\n\n" + changes + "\n## Reference\n\n" + tables + "\n" + foot
    import json
    data = json.load(open(os.path.join(ROOT, "out", "map.json")))
    nodes = data["nodes"]
    by_i = {n["i"]: n for n in nodes}

    def top(n):
        while by_i[n["parent"]]["parent"] is not None:
            n = by_i[n["parent"]]
        return n["name"]
    parts = [n for n in nodes if n["kind"] in ("Part", "MeshPart", "Marker")]
    trees = sum(1 for n in parts if "/Trees/" in path(n, by_i))
    subs = {"@@NPARTS@@": sum(1 for n in nodes if n["kind"] == "Part"),
            "@@NMESH@@": sum(1 for n in nodes if n["kind"] == "MeshPart"),
            "@@NMARK@@": sum(1 for n in nodes if n["kind"] == "Marker"),
            "@@TOTAL@@": "{:,}".format(len(parts)),
            "@@SHELL@@": sum(1 for n in parts if top(n) == "Shack"),
            "@@TREEPARTS@@": "{:,}".format(trees)}
    for k, v in subs.items():
        text = text.replace(k, str(v))
    assert "@@" not in text
    open(os.path.join(ROOT, "README.md"), "w").write(text)
    print("README.md", len(text.splitlines()), "lines")


if __name__ == "__main__":
    main()
