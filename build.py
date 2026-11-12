"""
Donkey feeding station - small scale printable model.

Run:  python3 build.py
Needs: pip install cadquery trimesh matplotlib

All dimensions are millimetres.  Parts are modelled in their assembled
position (x = width, y = depth with the shell front at y = 0, z = up) and are
re-oriented for printing when the STL files are written.

Parts
  shell   hollow station, open at the floor and at the front
  box     push box, hangs on two rails inside the shell
  driver  small block screwed to the box through a slot in the shell wall;
          it is the travel stop and it drags the bin lid
  bin     food bin, drops onto a dovetail on the side of the shell
  lid     sliding lid of the bin
"""
import os
import cadquery as cq

OUT = os.path.dirname(os.path.abspath(__file__))

# ----------------------------------------------------------------- parameters
TRAVEL = 40.0          # how far the box slides (= how far the lid opens)
PROTRUDE = 6.0         # box sticks out this far when fully pushed in
CLR = 0.35             # sliding clearance between printed parts

SH_W, SH_D, SH_H = 80.0, 110.0, 75.0   # shell outer size
WALL, ROOF, BACK = 7.0, 7.0, 5.0       # shell wall thicknesses
RAIL_Z = 50.0          # height of the rail centre line
SCREW_Z = 51.8         # height of the two driver screws
PILOT = 2.7            # hole an M3 screw cuts its own thread in
FREE = 3.4             # hole an M3 screw passes through freely
STOP_Y = 30.0          # position of the stop screw in the shell roof

BOX_L = 100.0
BIN_X0, BIN_X1 = 86.0, 154.0
BIN_Y0, BIN_Y1 = 10.0, 100.0
BIN_TOP = 50.0
LID_T = 4.0
DOVE_Y = 55.0          # centre of the dovetail that carries the bin


# -------------------------------------------------------------------- helpers
def block(x0, x1, y0, y1, z0, z1):
    return (cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False)
            .translate((x0, y0, z0)))


def prism(pts, axis, a0, a1):
    """Extrude a polygon along an axis.
    axis 'z': pts are (x, y);  'y': pts are (x, z);  'x': pts are (y, z)."""
    if axis == "z":
        return cq.Workplane("XY").polyline(pts).close().extrude(a1 - a0).translate((0, 0, a0))
    if axis == "y":
        s = cq.Workplane("XY").polyline(pts).close().extrude(a1 - a0).translate((0, 0, -a1))
        return s.rotate((0, 0, 0), (1, 0, 0), 90)
    s = cq.Workplane("XY").polyline(pts).close().extrude(a1 - a0).translate((0, 0, a0))
    return s.rotate((0, 0, 0), (1, 1, 1), 120)


def cyl_x(d, x0, x1, y, z):
    return (cq.Workplane("YZ").circle(d / 2).extrude(x1 - x0).translate((x0, y, z)))


def cyl_y(d, y0, y1, x, z):
    return (cq.Workplane("XZ").circle(d / 2).extrude(-(y1 - y0)).translate((x, y0, z)))


def cyl_z(d, z0, z1, x, y):
    return cq.Workplane("XY").circle(d / 2).extrude(z1 - z0).translate((x, y, z0))


XI0, XI1 = WALL, SH_W - WALL                 # shell inner walls
BX0, BX1 = XI0 + CLR, XI1 - CLR              # box outer sides
TONGUE = 3.0                                 # rail sticks out of the box side
T_TIP, T_BASE = 5.5, 8.5                     # rail half heights (45 degree flanks)
G_DEPTH = TONGUE + 0.4
G_TIP = T_TIP + 0.4
KEY_B0, KEY_B1 = 64.0, 90.0                  # driver position along the box
SCREW_B = (77.0, 85.0)
PLATE_X0, PLATE_X1 = SH_W + 0.5, SH_W + 5.0
LUG_X1 = 90.3


# ---------------------------------------------------------------------- shell
def make_shell():
    s = block(0, SH_W, 0, SH_D, 0, SH_H)
    s = s.cut(block(XI0, XI1, -1, SH_D - BACK, -1, SH_H - ROOF))
    # rail grooves, 45 degree flanks so they print without support
    gb = G_TIP + G_DEPTH + 0.1
    for sx, x in ((1, XI1), (-1, XI0)):
        s = s.cut(prism([(x - sx * 0.1, RAIL_Z - gb), (x + sx * G_DEPTH, RAIL_Z - G_TIP),
                         (x + sx * G_DEPTH, RAIL_Z + G_TIP), (x - sx * 0.1, RAIL_Z + gb)],
                        "y", -1, SH_D - BACK))
    # slot for the driver: closed at both ends, this is what keeps the box in.
    # Its lower face continues the 45 degree groove flank (prints clean upside down).
    xg = XI1 + G_DEPTH
    lo = RAIL_Z - G_TIP
    s = s.cut(prism([(xg - 0.05, lo - 0.05), (SH_W + 1, lo + (SH_W + 1 - xg)),
                     (SH_W + 1, RAIL_Z + G_TIP), (xg - 0.05, RAIL_Z + G_TIP)],
                    "y", KEY_B0 - PROTRUDE - TRAVEL - 0.5, KEY_B1 - PROTRUDE + 0.5))
    # second stop: screw through the roof into a slot in the box
    s = s.cut(cyl_z(PILOT, SH_H - ROOF - 1, SH_H + 1, SH_W / 2, STOP_Y))
    # dovetail that carries the bin
    d = prism([(SH_W - 0.5, DOVE_Y - 6), (SH_W + 5, DOVE_Y - 9),
               (SH_W + 5, DOVE_Y + 9), (SH_W - 0.5, DOVE_Y + 6)], "z", 0, 40)
    d = d.cut(prism([(SH_W, 40.01), (SH_W + 6, 40.01), (SH_W + 6, 34)], "y", DOVE_Y - 12, DOVE_Y + 12))
    return s.union(d)


# ------------------------------------------------------------------------ box
def make_box():
    """Modelled in 'box coordinates': front face at y = 0."""
    z0, z1 = 1.5, SH_H - ROOF - 0.5
    b = block(BX0, BX1, 0, BOX_L, z0, z1)
    b = b.cut(block(BX0 + 3, BX1 - 3, 4, BOX_L - 3, z0 - 1, z1 - 3))
    for sx, x in ((1, BX1), (-1, BX0)):
        b = b.union(prism([(x - sx * 0.5, RAIL_Z - T_BASE - 0.5), (x + sx * TONGUE, RAIL_Z - T_TIP),
                           (x + sx * TONGUE, RAIL_Z + T_TIP), (x - sx * 0.5, RAIL_Z + T_BASE + 0.5)],
                          "y", 0, BOX_L))
    # thick block inside for the driver screws (reaches the roof: no overhang)
    b = b.union(block(BX1 - 9, BX1 - 2.5, 70, 92, 44, z1 - 2.5))
    for sb in SCREW_B:
        b = b.cut(cyl_x(PILOT, BX1 - 10, BX1 + TONGUE + 1, sb, SCREW_Z))
    # pad + slot for the roof stop screw
    b = b.union(block(SH_W / 2 - 8, SH_W / 2 + 8, 28, 84, z1 - 7, z1 - 2.5))
    y_a = STOP_Y + PROTRUDE + 0.2
    y_b = STOP_Y + PROTRUDE + TRAVEL - 0.2
    slot = block(SH_W / 2 - 2, SH_W / 2 + 2, y_a, y_b, z1 - 5, z1 + 1)
    slot = slot.union(cyl_z(4, z1 - 5, z1 + 1, SH_W / 2, y_a)).union(cyl_z(4, z1 - 5, z1 + 1, SH_W / 2, y_b))
    b = b.cut(slot)
    # finger hole to pull the box back out
    b = b.cut(cyl_y(18, -1, 5, SH_W / 2, 30))
    return b


# --------------------------------------------------------------------- driver
def make_driver():
    """Box coordinates, like the box."""
    d = block(PLATE_X0, PLATE_X1, KEY_B0, KEY_B1, 44, 59)
    d = d.union(block(BX1 + TONGUE, PLATE_X0 + 0.1, KEY_B0, KEY_B1, SCREW_Z - 3.7, SCREW_Z + 3.7))
    d = d.union(block(PLATE_X1 - 0.1, LUG_X1, KEY_B0, KEY_B0 + 8, BIN_TOP + 0.5, 56))
    for sb in SCREW_B:
        d = d.cut(cyl_x(FREE, BX1, PLATE_X1 + 1, sb, SCREW_Z))
        d = d.cut(cyl_x(6.4, PLATE_X1 - 2.8, PLATE_X1 + 1, sb, SCREW_Z))
    return d


# ------------------------------------------------------------------------ bin
def make_bin():
    b = block(BIN_X0, BIN_X1, BIN_Y0, BIN_Y1, 0, BIN_TOP)
    b = b.cut(block(BIN_X0 + 8, BIN_X1 - 8, BIN_Y0 + 6, BIN_Y1 - 6, 3, BIN_TOP + 1))
    # mounting block with the dovetail socket (open top and bottom)
    m = block(SH_W + 0.4, BIN_X0 + 0.5, DOVE_Y - 17, DOVE_Y + 17, 0, 43)
    m = m.cut(prism([(SH_W, DOVE_Y - 6.35), (SH_W + 5.35, DOVE_Y - 9.56),
                     (SH_W + 5.35, DOVE_Y + 9.56), (SH_W, DOVE_Y + 6.35)], "z", -1, 44))
    b = b.union(m)
    t, h = BIN_TOP, BIN_TOP + LID_T
    # lid rails (45 degree undercut): right side full length, left side only at
    # the back so the driver lug can travel along the front part
    b = b.union(prism([(BIN_X1, t - 0.1), (BIN_X1, h + 0.5), (BIN_X1 - 8.5, h + 0.5),
                       (BIN_X1 - 8.5, h), (BIN_X1 - 4.5, t), (BIN_X1 - 4.5, t - 0.1)], "y", BIN_Y0, BIN_Y1))
    b = b.union(prism([(BIN_X0, t - 0.1), (BIN_X0, h + 0.5), (BIN_X0 + 8.5, h + 0.5),
                       (BIN_X0 + 8.5, h), (BIN_X0 + 4.5, t), (BIN_X0 + 4.5, t - 0.1)], "y", 73, BIN_Y1))
    b = b.union(prism([(BIN_Y0, t - 0.1), (BIN_Y0, h + 0.5), (BIN_Y0 + 6, h + 0.5),
                       (BIN_Y0 + 6, h), (BIN_Y0 + 2, t), (BIN_Y0 + 2, t - 0.1)], "x", 96.5, BIN_X1))
    return b


# ------------------------------------------------------------------------ lid
def make_lid():
    """Closed position."""
    t, h = BIN_TOP, BIN_TOP + LID_T
    xa, xb = BIN_X0 + 4.5 + CLR, BIN_X1 - 4.5 - CLR
    ya = BIN_Y0 + 2 + CLR
    l = prism([(xa, t), (xb, t), (xb - LID_T, h), (xa + LID_T, h)], "y", ya, BIN_Y1)
    l = l.intersect(prism([(ya, t), (ya + LID_T, h), (BIN_Y1 + 1, h), (BIN_Y1 + 1, t)], "x", 80, 160))
    # ear with the notch that drops over the driver lug
    lug_y = KEY_B0 - PROTRUDE - TRAVEL
    ear = block(BIN_X0 - 0.2, 96, ya, 31.8, t, h)
    ear = ear.cut(block(80, LUG_X1 + 0.4, lug_y - 0.3, lug_y + 8.3, t - 1, h + 1))
    l = l.union(ear)
    # grip ridge for the staff
    l = l.union(block(110, 130, 89, 92, h - 0.1, h + 2.5))
    return l


# ------------------------------------------------------------------ build all
shell, box, driver, bin_, lid = make_shell(), make_box(), make_driver(), make_bin(), make_lid()


def placed(part, y):
    return part.translate((0, y, 0))


Y_IN, Y_OUT = -PROTRUDE, -PROTRUDE - TRAVEL


def vol(a, b):
    try:
        return a.intersect(b).val().Volume()
    except Exception:
        return 0.0


def check():
    ok = True
    cases = []
    for name, by, ly in (("box out / lid closed", Y_OUT, 0), ("half way", Y_OUT + 20, 20),
                         ("box in / lid open", Y_IN, TRAVEL)):
        b, d, l = placed(box, by), placed(driver, by), placed(lid, ly)
        cases += [(name, "shell-box", shell, b), (name, "shell-driver", shell, d),
                  (name, "box-driver", b, d), (name, "bin-driver", bin_, d),
                  (name, "bin-lid", bin_, l), (name, "lid-driver", l, d),
                  (name, "lid-shell", l, shell), (name, "bin-shell", bin_, shell),
                  (name, "bin-box", bin_, b)]
    for name, pair, a, b in cases:
        v = vol(a, b)
        if v > 1e-3:
            ok = False
            print(f"  COLLISION {name}: {pair} {v:.2f} mm3")
    # things that MUST be blocked
    must = [
        ("lid cannot open while box is out", placed(lid, 3), placed(driver, Y_OUT)),
        ("lid cannot be lifted off", lid.translate((0, 0, 2)), bin_),
        ("box cannot be pulled out further", shell, placed(driver, Y_OUT - 2)),
        ("box cannot be pushed in further", shell, placed(driver, Y_IN + 2)),
        ("box cannot drop out of the floor", shell, placed(box, Y_IN).translate((0, 0, -2))),
        ("bin cannot be pulled sideways", shell, bin_.translate((2, 0, 0))),
    ]
    for name, a, b in must:
        v = vol(a, b)
        print(f"  {'ok ' if v > 1e-3 else 'FAIL'} {name}")
        ok = ok and v > 1e-3
    return ok


def to_print(part, kind):
    if kind == "flip":                       # print standing on its roof
        part = part.rotate((0, 0, 0), (1, 0, 0), 180)
    elif kind == "front_down":               # print standing on its front end
        part = part.rotate((0, 0, 0), (1, 0, 0), 90)
    bb = part.val().BoundingBox()
    return part.translate((-bb.xmin, -bb.ymin, -bb.zmin))


if __name__ == "__main__":
    print("checking fit...")
    good = check()
    print("fit check:", "PASSED" if good else "FAILED")

    os.makedirs(f"{OUT}/stl", exist_ok=True)
    os.makedirs(f"{OUT}/step", exist_ok=True)
    for name, part, kind in (("1_shell", shell, "flip"), ("2_box", box, "flip"),
                             ("3_driver", driver, "front_down"), ("4_bin", bin_, None),
                             ("5_lid", lid, None)):
        p = to_print(part, kind)
        bb = p.val().BoundingBox()
        cq.exporters.export(p, f"{OUT}/stl/{name}.stl", tolerance=0.02, angularTolerance=0.15)
        print(f"  {name}: {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm, {p.val().Volume()/1000:.0f} cm3 solid")

    for tag, by, ly in (("closed", Y_OUT, 0), ("open", Y_IN, TRAVEL)):
        asm = cq.Assembly()
        asm.add(shell, name="shell", color=cq.Color(0.55, 0.6, 0.65))
        asm.add(placed(box, by), name="box", color=cq.Color(0.9, 0.55, 0.15))
        asm.add(placed(driver, by), name="driver", color=cq.Color(0.8, 0.15, 0.15))
        asm.add(bin_, name="bin", color=cq.Color(0.25, 0.55, 0.3))
        asm.add(placed(lid, ly), name="lid", color=cq.Color(0.95, 0.85, 0.3))
        asm.save(f"{OUT}/step/assembly_{tag}.step")
        for n, p in (("shell", shell), ("box", placed(box, by)), ("driver", placed(driver, by)),
                     ("bin", bin_), ("lid", placed(lid, ly))):
            os.makedirs(f"{OUT}/step/_tmp", exist_ok=True)
            cq.exporters.export(p, f"{OUT}/step/_tmp/{tag}_{n}.stl", tolerance=0.05, angularTolerance=0.2)
    total_y = (BIN_Y1 + TRAVEL) - (Y_OUT)
    print(f"overall size: {BIN_X1:.0f} wide x {total_y:.0f} deep x {SH_H:.0f} high (limit 200 x 200 x 150)")
