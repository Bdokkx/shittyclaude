"""Markdown table of the props for the README (parts, triangles, what each one is),
from out/props.json and the docstrings in blender/pdefs.py.

    python tools/readme_table.py out/props.json
"""
import ast
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "..", "blender", "pdefs.py")).read()
docs = {}
for node in ast.parse(src).body:
    if isinstance(node, ast.FunctionDef):
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and getattr(dec.func, "id", "") == "prop" and dec.args:
                doc = ast.get_docstring(node) or ""
                docs[dec.args[0].value] = " ".join(doc.split())
props = json.load(open(sys.argv[1]))
print("| Prop | Parts | Triangles | Look |")
print("|---|---|---|---|")
for p in props:
    if p["Kind"] != "Prop":
        continue
    names = []
    for q in p["Parts"]:
        if q["Name"] not in names:
            names.append(q["Name"])
    print("| %s | %s | %s | %s |" % (p["Id"], ", ".join(names), "{:,}".format(p["Tris"]), docs.get(p["Id"], "")))
print()
print("| NPC piece | Parts | Triangles | Look |")
print("|---|---|---|---|")
for p in props:
    if p["Kind"] == "Prop":
        continue
    names = []
    for q in p["Parts"]:
        if q["Name"] not in names:
            names.append(q["Name"])
    print("| %s | %s | %s | %s |" % (p["Id"], ", ".join(names), "{:,}".format(p["Tris"]), docs.get(p["Id"], "")))
