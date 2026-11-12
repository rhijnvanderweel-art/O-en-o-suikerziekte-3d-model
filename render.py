"""Renders preview pictures of the assembly (run build.py first)."""
import os, numpy as np, trimesh
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
OUT = os.path.dirname(os.path.abspath(__file__))
COL = {"shell": (.6, .65, .7), "box": (.92, .55, .15), "driver": (.85, .15, .15),
       "bin": (.3, .6, .35), "lid": (.95, .85, .3)}
L = np.array([0.4, -0.6, 0.7]); L /= np.linalg.norm(L)

def draw(ax, tag, elev, azim, hide=()):
    tris, cols = [], []
    for n, c in COL.items():
        if n in hide:
            continue
        m = trimesh.load(f"{OUT}/step/_tmp/{tag}_{n}.stl")
        m = m.subdivide_to_size(12)
        sh = 0.45 + 0.55 * np.abs(m.face_normals @ L)
        tris.append(m.triangles); cols.append(np.clip(np.outer(sh, c), 0, 1))
    ax.add_collection3d(Poly3DCollection(np.concatenate(tris), facecolors=np.concatenate(cols), edgecolors="none"))
    ax.set_xlim(-20, 170); ax.set_ylim(-50, 140); ax.set_zlim(-60, 130)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(elev, azim); ax.set_axis_off()

def fig(name, views, titles):
    f = plt.figure(figsize=(7 * len(views), 7))
    for i, (v, t) in enumerate(zip(views, titles)):
        ax = f.add_subplot(1, len(views), i + 1, projection="3d", computed_zorder=True)
        draw(ax, **v); ax.set_title(t, fontsize=15, y=0.92)
    f.subplots_adjust(0, 0, 1, 1, 0, 0)
    f.savefig(f"{OUT}/images/{name}.png", dpi=110); plt.close(f)

os.makedirs(f"{OUT}/images", exist_ok=True)
fig("overview", [dict(tag="closed", elev=28, azim=-60), dict(tag="open", elev=28, azim=-60)],
    ["Box pulled out - bin closed", "Box pushed in - bin open"])
fig("top", [dict(tag="closed", elev=89, azim=-90), dict(tag="open", elev=89, azim=-90)],
    ["Top view, closed", "Top view, open"])
fig("back_side", [dict(tag="closed", elev=25, azim=40), dict(tag="open", elev=25, azim=40)],
    ["Rear view, closed", "Rear view, open"])
fig("mechanism", [dict(tag="closed", elev=20, azim=-35, hide=("bin",)), dict(tag="open", elev=20, azim=-35, hide=("bin",))],
    ["Bin hidden: red driver block holds the lid shut", "Box pushed in: driver drags the lid open"])
for f in sorted(os.listdir(f"{OUT}/stl")):
    m = trimesh.load(f"{OUT}/stl/{f}")
    print(f, "watertight" if m.is_watertight else "NOT WATERTIGHT", len(m.faces), "faces")
