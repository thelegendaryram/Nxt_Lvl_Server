# menu.py
import nuke
import os

ROOT = os.path.dirname(__file__)
GIZMOS_PATH = os.path.join(ROOT, "gizmos")
PYTHON_PATH = os.path.join(ROOT, "python")


# --------------------------------------------------
# TOP MENU (File / Edit / Render ...)
# --------------------------------------------------

main_menu = nuke.menu("Nuke")
nxt_menu = main_menu.addMenu("NXT_LVL")

gizmos_menu = nxt_menu.addMenu("Gizmos")
#toolsets_menu = nxt_menu.addMenu("Toolsets")
#python_menu = nxt_menu.addMenu("Python")

# --------------------------------------------------
# AUTO LOAD GIZMOS
# --------------------------------------------------

def build_gizmo_menu(base_path, menu):
    for root, dirs, files in os.walk(base_path):
        rel = os.path.relpath(root, base_path)
        current_menu = menu

        if rel != ".":
            for folder in rel.split(os.sep):
                current_menu = current_menu.addMenu(folder)

        for f in files:
            if f.endswith(".gizmo"):
                gizmo = os.path.splitext(f)[0]
                current_menu.addCommand(
                    gizmo,
                    f"nuke.createNode('{gizmo}')"
                )

if os.path.exists(GIZMOS_PATH):
    build_gizmo_menu(GIZMOS_PATH, gizmos_menu)
