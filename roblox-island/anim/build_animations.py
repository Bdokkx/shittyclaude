"""Write build/animations.json (all remade sequences) for tools/export_animations.luau."""
import json
import os

from anims import build_all

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    seqs = [s.to_json() for s in build_all()]
    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    json.dump(seqs, open(os.path.join(ROOT, "build", "animations.json"), "w"))
    for s in seqs:
        print("%-11s %5.2fs %-4s %-8s %3d keyframes" % (s["name"], s["length"], "loop" if s["loop"] else "once",
                                                       s["priority"], len(s["keyframes"])))
