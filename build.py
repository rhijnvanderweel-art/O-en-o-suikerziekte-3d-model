"""
Donkey feeding station - small scale printable model (version 2).

Run:  python3 build.py        (needs: pip install cadquery trimesh matplotlib)

All dimensions are millimetres.  Parts are modelled in their assembled
position (x = width, y = depth with the shell front at y = 0, z = up) and are
re-oriented for printing when the STL files are written.

Parts
  shell   hollow station, open at the floor and at the front. Two side rails
          and one top rail (dovetail on the roof) carry the box.
  box     push box. It hangs from the rails 15 mm above the ground.
  driver  block screwed to the box through a slot in the shell wall. The
          closed slot ends are the travel stops; its lug drives the bin lid.
  bin     food bin with a support tail behind it. The lid rails run over the
          bin and the tail, so the lid can slide fully off the opening and
          still be carried along its whole length.
  lid     plain sliding lid, slides in from the back of the tail
  catch   screwed onto the lid; its notch drops over the driver lug
"""
import os
import cadquery as cq

OUT = os.path.dirname(os.path.abspath(__file__))

# ----------------------------------------------------------------- parameters
TRAVEL = 60.0          # box travel = lid travel (longer than the bin opening)
PROTRUDE = 6.0         # box sticks out this far when fully pushed in
CLR = 0.35             # sliding clearance between printed parts
PILOT = 2.7            # hole an M3 screw cuts its own thread in
FREE = 3.4             # hole an M3 screw passes through freely
HEAD = 6.4             # counterbore for an M3 screw head (max 6 mm head)

SH_W, SH_D, SH_H = 80.0, 120.0, 90.0   # shell outer size
WALL, ROOF, BACK = 7.0, 9.0, 5.0
RAIL_Z = 48.0          # side rail centre line
SCREW_Z = 49.8         # driver screws
STOP_X, STOP_Y = 16.0, 20.0            # roof stop screw

BOX_Z0 = 15.0          # ground clearance under the box
BOX_L = 120.0
BOX_TOP_T = 6.0        # box top wall (holds the top-rail groove)

TT_Z = SH_H - ROOF     # roof inner face (81)
TT_H = 3.5             # top rail tongue height
TT_HW = 6.0            # top rail tongue half width at the roof

BIN_X0, BIN_X1 = 93.0, 163.0
BIN_Y0, BIN_Y1 = 0.0, 67.0             # food bin
TAIL_Y1 = 127.0                        # end of the lid support tail
BIN_TOP = 50.0
SIDE_T, END_T, FLOOR_T = 8.0, 5.0, 3.0
LID_T = 6.0
LID_L = 63.0
DOVE_Y = 75.0          # centre of the dovetail that carries the bin

# derived
XI0, XI1 = WALL, SH_W - WALL           # shell inner walls
BX0, BX1 = XI0 + CLR, XI1 - CLR        # box sides
BZ1 = TT_Z - 0.5                       # box top
TONGUE = 3.0
T_TIP, T_BASE = 5.5, 8.5
G_DEPTH = TONGUE + 0.4
G_TIP = T_TIP + 0.4
Y_IN, Y_OUT = -PROTRUDE, -PROTRUDE - TRAVEL

PLATE_X0, PLATE_X1 = SH_W + 0.5, SH_W + 5.5
LUG_X1 = BIN_X0 - 0.5
H_LID = BIN_TOP + LID_T                # lid top (56)
RAIL_TOP = H_LID + 0.5
LUG_Z0, LUG_Z1 = RAIL_TOP + 0.5, RAIL_TOP + 6.5        # 57 .. 63
LID_Y0 = BIN_Y0 + 3 + CLR              # lid front when closed
LUG_Y0 = 10.3                          # lug front, box out (shell coordinates)
KEY_B0 = LUG_Y0 - Y_OUT                # same, box coordinates
KEY_B1 = KEY_B0 + 26.0
SCREW_B = (KEY_B0 + 8.0, KEY_B0 + 20.0)
CATCH_Y0, CATCH_Y1 = LID_Y0 + 0.4, 26.0
CATCH_SCREWS = ((112.0, 7.5), (112.0, 22.0))


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
    return cq.Workplane("YZ").circle(d / 2).extrude(x1 - x0).translate((x0, y, z))


def cyl_z(d, z0, z1, x, y):
    return cq.Workplane("XY").circle(d / 2).extrude(z1 - z0).translate((x, y, z0))


def teardrop_y(d, y0, y1, x, z):
    """Horizontal hole along y with a 45 degree point at the bottom, so it
    prints cleanly when the part is printed upside down."""
    r = d / 2
    c = cq.Workplane("XZ").circle(r).extrude(-(y1 - y0)).translate((x, y0, z))
    k = r / 2 ** 0.5
    tip = prism([(x - k, z - k), (x, z - r * 2 ** 0.5), (x + k, z - k), (x, z)], "y", y0, y1)
    return c.union(tip)


# ---------------------------------------------------------------------- shell
def make_shell():
    s = block(0, SH_W, 0, SH_D, 0, SH_H)
    s = s.cut(block(XI0, XI1, -1, SH_D - BACK, -1, TT_Z))
    # side rail grooves (45 degree flanks)
    gb = G_TIP + G_DEPTH + 0.1
    for sx, x in ((1, XI1), (-1, XI0)):
        s = s.cut(prism([(x - sx * 0.1, RAIL_Z - gb), (x + sx * G_DEPTH, RAIL_Z - G_TIP),
                         (x + sx * G_DEPTH, RAIL_Z + G_TIP), (x - sx * 0.1, RAIL_Z + gb)],
                        "y", -1, SH_D - BACK))
    # top rail: dovetail tongue hanging from the roof (widens downward, 45 deg)
    cx = SH_W / 2
    s = s.union(prism([(cx - TT_HW, TT_Z + 0.1), (cx - TT_HW - TT_H, TT_Z - TT_H),
                       (cx + TT_HW + TT_H, TT_Z - TT_H), (cx + TT_HW, TT_Z + 0.1)],
                      "y", 0.5, SH_D - BACK + 0.1))
    # slot for the driver, closed at both ends = travel stops
    xg = XI1 + G_DEPTH
    lo = RAIL_Z - G_TIP
    s = s.cut(prism([(xg - 0.05, lo - 0.05), (SH_W + 1, lo + (SH_W + 1 - xg)),
                     (SH_W + 1, RAIL_Z + G_TIP), (xg - 0.05, RAIL_Z + G_TIP)],
                    "y", KEY_B0 + Y_OUT - 0.5, KEY_B1 + Y_IN + 0.5))
    # second stop: screw through the roof into a slot in the box top
    s = s.cut(cyl_z(PILOT, TT_Z - 1, SH_H + 1, STOP_X, STOP_Y))
    # dovetail that carries the bin (top chamfered for printing upside down)
    d = prism([(SH_W - 0.5, DOVE_Y - 6), (SH_W + 5.5, DOVE_Y - 9),
               (SH_W + 5.5, DOVE_Y + 9), (SH_W - 0.5, DOVE_Y + 6)], "z", 0, 36)
    d = d.cut(prism([(SH_W, 36.01), (SH_W + 6, 36.01), (SH_W + 6, 30)], "y", DOVE_Y - 12, DOVE_Y + 12))
    return s.union(d)


# ------------------------------------------------------------------------ box
def make_box():
    """Box coordinates: front face at y = 0."""
    z0, z1 = BOX_Z0, BZ1
    b = block(BX0, BX1, 0, BOX_L, z0, z1)
    b = b.cut(block(BX0 + 3, BX1 - 3, 4, BOX_L - 3, z0 - 1, z1 - BOX_TOP_T))
    # side rail tongues
    for sx, x in ((1, BX1), (-1, BX0)):
        b = b.union(prism([(x - sx * 0.5, RAIL_Z - T_BASE - 0.5), (x + sx * TONGUE, RAIL_Z - T_TIP),
                           (x + sx * TONGUE, RAIL_Z + T_TIP), (x - sx * 0.5, RAIL_Z + T_BASE + 0.5)],
                          "y", 0, BOX_L))
    # top rail groove (dovetail, 0.5 mm clearance each side, 0.4 mm at the bottom)
    cx = SH_W / 2

    def gh(z):
        return TT_HW + 0.5 + (TT_Z - z)
    zb = TT_Z - TT_H - 0.4
    b = b.cut(prism([(cx - gh(z1 + 0.1), z1 + 0.1), (cx - gh(zb), zb),
                     (cx + gh(zb), zb), (cx + gh(z1 + 0.1), z1 + 0.1)], "y", -1, BOX_L + 1))
    # block inside for the driver screws (hangs from the top wall: no overhang)
    b = b.union(block(BX1 - 9, BX1 - 2.5, KEY_B0 + 2, KEY_B1 - 2, 42, z1 - BOX_TOP_T + 0.1))
    for sb in SCREW_B:
        b = b.cut(cyl_x(PILOT, BX1 - 10, BX1 + TONGUE + 1, sb, SCREW_Z))
    # slot for the roof stop screw
    y_a = STOP_Y + PROTRUDE + 0.2
    y_b = STOP_Y + PROTRUDE + TRAVEL - 0.2
    slot = block(STOP_X - 2, STOP_X + 2, y_a, y_b, z1 - 5, z1 + 1)
    slot = slot.union(cyl_z(4, z1 - 5, z1 + 1, STOP_X, y_a)).union(cyl_z(4, z1 - 5, z1 + 1, STOP_X, y_b))
    b = b.cut(slot)
    # finger hole to pull the box back out
    b = b.cut(teardrop_y(18, -1, 5, SH_W / 2, 38))
    return b


# --------------------------------------------------------------------- driver
def make_driver():
    """Box coordinates, like the box."""
    d = block(PLATE_X0, PLATE_X1, KEY_B0, KEY_B1, 42, LUG_Z1)
    d = d.union(block(BX1 + TONGUE, PLATE_X0 + 0.1, KEY_B0, KEY_B1, SCREW_Z - 3.7, SCREW_Z + 3.7))
    d = d.union(block(PLATE_X1 - 0.1, LUG_X1, KEY_B0, KEY_B0 + 8, LUG_Z0, LUG_Z1))   # lug
    for sb in SCREW_B:
        d = d.cut(cyl_x(FREE, BX1, PLATE_X1 + 1, sb, SCREW_Z))
        d = d.cut(cyl_x(HEAD, PLATE_X1 - 2.8, PLATE_X1 + 1, sb, SCREW_Z))
    return d


# ------------------------------------------------------------------------ bin
def make_bin():
    t, h = BIN_TOP, H_LID
    b = block(BIN_X0, BIN_X1, BIN_Y0, BIN_Y1, 0, t)
    b = b.cut(block(BIN_X0 + SIDE_T, BIN_X1 - SIDE_T, BIN_Y0 + END_T, BIN_Y1 - END_T, FLOOR_T, t + 1))
    # support tail: side walls, floor and end wall carry the open lid
    b = b.union(block(BIN_X0, BIN_X0 + SIDE_T, BIN_Y1 - 0.1, TAIL_Y1, 0, t))
    b = b.union(block(BIN_X1 - SIDE_T, BIN_X1, BIN_Y1 - 0.1, TAIL_Y1, 0, t))
    b = b.union(block(BIN_X0, BIN_X1, BIN_Y1 - 0.1, TAIL_Y1, 0, FLOOR_T))
    b = b.union(block(BIN_X0, BIN_X1, TAIL_Y1 - END_T, TAIL_Y1, 0, t))
    # lid rails, 45 degree undercut, over the whole bin + tail
    w = 4.5 + LID_T
    b = b.union(prism([(BIN_X1, t - 0.1), (BIN_X1, h + 0.5), (BIN_X1 - w, h + 0.5),
                       (BIN_X1 - w, h), (BIN_X1 - 4.5, t), (BIN_X1 - 4.5, t - 0.1)], "y", BIN_Y0, TAIL_Y1))
    b = b.union(prism([(BIN_X0, t - 0.1), (BIN_X0, h + 0.5), (BIN_X0 + w, h + 0.5),
                       (BIN_X0 + w, h), (BIN_X0 + 4.5, t), (BIN_X0 + 4.5, t - 0.1)], "y", BIN_Y0, TAIL_Y1))
    # front lip: the closed lid stops against it
    b = b.union(block(BIN_X0 + 4, BIN_X1 - 4, BIN_Y0, BIN_Y0 + 3, t - 0.1, h + 0.5))
    # mounting block with the dovetail socket (open top and bottom)
    m = block(SH_W + 0.4, BIN_X0 + 0.5, DOVE_Y - 17, DOVE_Y + 17, 0, 41)
    m = m.cut(prism([(SH_W, DOVE_Y - 6.35), (SH_W + 5.85, DOVE_Y - 9.6),
                     (SH_W + 5.85, DOVE_Y + 9.6), (SH_W, DOVE_Y + 6.35)], "z", -1, 42))
    return b.union(m)


# ------------------------------------------------------------------- lid + catch
def lid_body():
    """Plain dovetail lid, closed position. Nothing sticks out, so it slides
    in from the back of the tail underneath both undercut rails."""
    t, h = BIN_TOP, H_LID
    xa, xb = BIN_X0 + 4.5 + CLR, BIN_X1 - 4.5 - CLR
    return prism([(xa, t), (xb, t), (xb - LID_T, h), (xa + LID_T, h)], "y", LID_Y0, LID_Y0 + LID_L)


def make_lid():
    l = lid_body()
    l = l.union(block(120, 140, LID_Y0 + LID_L - 6, LID_Y0 + LID_L - 3, H_LID - 0.1, H_LID + 2.5))
    for x, y in CATCH_SCREWS:
        l = l.cut(cyl_z(PILOT, BIN_TOP - 1, H_LID + 1, x, y))
    return l


def make_catch():
    """Screwed onto the lid after the lid is in the rails. It reaches over the
    left rail and its notch drops over the driver lug. Closed position."""
    rail_in = BIN_X0 + 4.5 + LID_T            # inner top edge of the left rail
    c = block(PLATE_X1 + 0.4, rail_in + 0.5, CATCH_Y0, CATCH_Y1, RAIL_TOP + 0.4, LUG_Z1)
    c = c.union(block(rail_in + 0.4, 120, CATCH_Y0, CATCH_Y1, H_LID, LUG_Z1))
    c = c.cut(block(80, LUG_X1 + 0.4, LUG_Y0 - 0.3, LUG_Y0 + 8.3, 0, 100))       # lug notch
    for x, y in CATCH_SCREWS:
        c = c.cut(cyl_z(FREE, 0, 100, x, y))
        c = c.cut(cyl_z(HEAD, LUG_Z1 - 2.8, 100, x, y))
    return c


# ------------------------------------------------------------------ build all
shell, box, driver, bin_, lid, catch = (make_shell(), make_box(), make_driver(), make_bin(),
                                        make_lid(), make_catch())


def placed(part, y):
    return part.translate((0, y, 0))


def vol(a, b):
    try:
        return a.intersect(b).val().Volume()
    except Exception:
        return 0.0


def check():
    ok = True

    def clash(label, a, b):
        v = vol(a, b)
        if v > 1e-3:
            print(f"    collision: {label} ({v:.2f} mm3)")
        return v > 1e-3

    def step(name, hits):
        nonlocal ok
        print(f"  {'FAIL' if hits else 'ok '} {name}")
        ok = ok and not hits

    print(" assembly")
    step("1. box slides into the shell from the front",
         sum(clash(f"box at {y}", placed(box, Y_OUT - y), shell) for y in range(0, 126, 3)))
    step("2. driver block goes through the wall slot and against the box",
         sum(clash(f"driver x+{x}", placed(driver, Y_OUT).translate((x, 0, 0)), o)
             for x in range(0, 16) for o in (shell, placed(box, Y_OUT))))
    step("3. lid slides into the rails from the back of the tail",
         sum(clash(f"lid at {s}", placed(lid, s), bin_) for s in range(0, 132, 2)))
    step("4. catch is put on the lid from above",
         sum(clash(f"catch z+{z}", catch.translate((0, 0, z)), o)
             for z in range(0, 16) for o in (bin_, lid)))
    step("5. bin with lid and catch is lowered onto the station (box out)",
         sum(clash(f"bin z+{z} {n}", p.translate((0, 0, z)), o)
             for z in range(0, 72, 2)
             for n, p in (("bin", bin_), ("lid", lid), ("catch", catch))
             for o in (shell, placed(box, Y_OUT), placed(driver, Y_OUT))))
    print(" working")
    hits = 0
    for s in range(0, int(TRAVEL) + 1, 2):
        b, d, l, c = placed(box, Y_OUT + s), placed(driver, Y_OUT + s), placed(lid, s), placed(catch, s)
        parts = (("shell", shell), ("box", b), ("driver", d), ("bin", bin_), ("lid", l), ("catch", c))
        for i in range(len(parts)):
            for j in range(i + 1, len(parts)):
                hits += clash(f"travel {s}: {parts[i][0]}-{parts[j][0]}", parts[i][1], parts[j][1])
    step(f"box and lid move together over the full {TRAVEL:.0f} mm", hits)
    opening_back = BIN_Y1 - END_T
    step(f"open lid fully clears the food opening (lid front {LID_Y0 + TRAVEL:.1f} > {opening_back:.0f})",
         LID_Y0 + TRAVEL <= opening_back)
    step(f"open lid lies fully on the rails (lid back {LID_Y0 + LID_L + TRAVEL:.1f} <= {TAIL_Y1:.0f})",
         LID_Y0 + LID_L + TRAVEL > TAIL_Y1)
    print(" must be blocked")
    must = [
        ("lid cannot open while box is out", placed(catch, 1), placed(driver, Y_OUT)),
        ("lid cannot close while box is in", placed(catch, TRAVEL - 1), placed(driver, Y_IN)),
        ("lid cannot be lifted off", lid.translate((0, 0, 2)), bin_),
        ("lid cannot slide off the front", placed(lid, -1), bin_),
        ("box cannot be pulled out further", shell, placed(driver, Y_OUT - 2)),
        ("box cannot be pushed in further", shell, placed(driver, Y_IN + 2)),
        ("box cannot drop down out of the shell", shell, placed(box, Y_IN).translate((0, 0, -2))),
        ("box hangs on the top rail", shell, placed(box, Y_IN).translate((0, 0, -0.6))),
        ("bin cannot be pulled sideways", shell, bin_.translate((2, 0, 0))),
    ]
    for name, a, b in must:
        step(name, vol(a, b) <= 1e-3)
    return ok


def to_print(part, kind):
    if kind == "flip":                       # upside down
        part = part.rotate((0, 0, 0), (1, 0, 0), 180)
    elif kind == "front_down":               # standing on its front end
        part = part.rotate((0, 0, 0), (1, 0, 0), 90)
    bb = part.val().BoundingBox()
    return part.translate((-bb.xmin, -bb.ymin, -bb.zmin))


if __name__ == "__main__":
    print("checking fit...")
    good = check()
    print("fit check:", "PASSED" if good else "FAILED")

    import shutil
    for d in ("stl", "step"):
        shutil.rmtree(f"{OUT}/{d}", ignore_errors=True)
        os.makedirs(f"{OUT}/{d}")
    for name, part, kind in (("1_shell", shell, "flip"), ("2_box", box, "flip"),
                             ("3_driver", driver, "front_down"), ("4_bin", bin_, None),
                             ("5_lid", lid, None), ("6_lid_catch", catch, "flip")):
        p = to_print(part, kind)
        bb = p.val().BoundingBox()
        cq.exporters.export(p, f"{OUT}/stl/{name}.stl", tolerance=0.02, angularTolerance=0.15)
        print(f"  {name}: {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm, {p.val().Volume()/1000:.0f} cm3 solid")

    os.makedirs(f"{OUT}/step/_tmp", exist_ok=True)
    for tag, s in (("closed", 0.0), ("open", TRAVEL)):
        pos = {"shell": shell, "box": placed(box, Y_OUT + s), "driver": placed(driver, Y_OUT + s),
               "bin": bin_, "lid": placed(lid, s), "catch": placed(catch, s)}
        cols = {"shell": (0.55, 0.6, 0.65), "box": (0.9, 0.55, 0.15), "driver": (0.8, 0.15, 0.15),
                "bin": (0.25, 0.55, 0.3), "lid": (0.95, 0.85, 0.3), "catch": (0.2, 0.35, 0.8)}
        asm = cq.Assembly()
        for n, p in pos.items():
            asm.add(p, name=n, color=cq.Color(*cols[n]))
            cq.exporters.export(p, f"{OUT}/step/_tmp/{tag}_{n}.stl", tolerance=0.05, angularTolerance=0.2)
        asm.export(f"{OUT}/step/assembly_{tag}.step")
    print(f"overall size: {BIN_X1:.0f} wide (x) x {TAIL_Y1 - Y_OUT:.0f} deep (y) x {SH_H:.0f} high"
          f"  (limit 200 x 200 x 150)")
