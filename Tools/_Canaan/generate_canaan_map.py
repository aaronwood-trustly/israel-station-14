#!/usr/bin/env python3
"""
Generates Resources/Maps/_NF/POI/canaan.yml, the Canaan point of interest.

The layout is defined in code below (tiles, walls, props, power) and written out in the
engine's grid map format (format 7). Re-run this after editing the layout:

    python3 Tools/_Canaan/generate_canaan_map.py

Once the map has been opened and saved in the in-game mapper, prefer editing it there and
treat this script as the record of the original layout.

Layout (north is up), 33 x 25 tiles:
  NW  Abraham's tent at Mamre: open on all four sides, oaks, a hearth
  NE  Bethel (Jacob's stone pillow and pillar), Jacob's kitchen, the goat pen
  C   The well of Beersheba, where the roads meet
  SW  Isaac's fields of Gerar and the well of Rehoboth
  SE  The storehouse: power, gravity, air, spare robes
  E/W Docking gates for visiting ships
"""

import base64
import math
import struct
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Resources" / "Maps" / "_NF" / "POI" / "canaan.yml"

W, H = 33, 25  # columns 0..32 (west to east), rows 0..24 (north to south)

# Rotations (radians). 0 = facing south. Positive = counter-clockwise.
R0, R90, R180, R270 = 0.0, math.pi / 2, math.pi, -math.pi / 2

# Tile names (left) mapped to stable tilemap ids (right).
TILEMAP = {
    "Space": 0,
    "FloorDesert": 1,
    "FloorLowDesert": 2,
    "FloorWood": 3,
    "FloorAstroGrass": 4,
    "Plating": 5,
}
TILE_VARIANTS = {"FloorDesert": 6, "FloorLowDesert": 6, "FloorWood": 4, "FloorAstroGrass": 4, "Plating": 1}


def to_world(col, row):
    """Grid tile coordinates for a layout cell. Center cell (16, 12) is tile (0, 0)."""
    return col - 16, 12 - row


tiles = {}      # (col,row) -> tile name
walls = set()   # (col,row) cells with a wall (wall, window, or door frame)
entities = []   # (proto, col, row, rot, extra_components, offset)
solid = {}      # (col,row) -> proto, for overlap checking of blocking things
powered = []    # (col,row) cells holding something that draws power


def tile(col, row, name):
    tiles[(col, row)] = name


def rect_tiles(c0, r0, c1, r1, name):
    for c in range(c0, c1 + 1):
        for r in range(r0, r1 + 1):
            tile(c, r, name)


def ent(proto, col, row, rot=0.0, extra=None, offset=(0.0, 0.0), blocking=False, power=False):
    if blocking:
        if (col, row) in solid:
            raise ValueError(f"{proto} at {(col, row)} overlaps {solid[(col, row)]}")
        solid[(col, row)] = proto
    if power:
        powered.append((col, row))
    entities.append((proto, col, row, rot, extra or [], offset))


def named(name, desc=None):
    comp = {"type": "MetaData", "name": name}
    if desc:
        comp["desc"] = desc
    return comp


# ---------------------------------------------------------------------------
# Ground
# ---------------------------------------------------------------------------
rect_tiles(0, 0, W - 1, H - 1, "FloorDesert")

# Roads of beaten earth: east-west between the gates, north-south through the well.
rect_tiles(1, 11, W - 2, 13, "FloorLowDesert")
rect_tiles(15, 1, 17, H - 2, "FloorLowDesert")

# The oasis around the well of Beersheba.
rect_tiles(12, 9, 20, 15, "FloorAstroGrass")

# Isaac's fields.
rect_tiles(1, 15, 12, 23, "FloorAstroGrass")

# Inside the goat pen.
rect_tiles(22, 6, 30, 9, "FloorAstroGrass")

# Abraham's tent floor, Jacob's kitchen floor, the storehouse floor.
rect_tiles(3, 2, 10, 7, "FloorWood")
rect_tiles(26, 1, 31, 4, "FloorWood")
rect_tiles(22, 17, 31, 23, "FloorWood")

# ---------------------------------------------------------------------------
# Outer wall, windows, docking gates
# ---------------------------------------------------------------------------
DOCKS = [(0, 11, R270), (0, 13, R270), (W - 1, 11, R90), (W - 1, 13, R90)]
dock_cells = {(c, r) for c, r, _ in DOCKS}
window_cells = set()
for c in range(5, W - 3, 6):
    window_cells |= {(c, 0), (c, H - 1)}
window_cells |= {(0, 5), (0, 19), (W - 1, 5)}

for c in range(W):
    for r in range(H):
        if c in (0, W - 1) or r in (0, H - 1):
            tile(c, r, "Plating")
            walls.add((c, r))
            if (c, r) in dock_cells:
                continue
            if (c, r) in window_cells:
                ent("Grille", c, r, blocking=True)
                ent("ReinforcedWindow", c, r)
            else:
                ent("WallSandstone", c, r, blocking=True)

for c, r, rot in DOCKS:
    ent("AirlockGlassShuttle", c, r, rot, blocking=True, power=True)
    ent("AtmosDeviceFanDirectional", c, r, rot)

# ---------------------------------------------------------------------------
# NW: Abraham's tent at Mamre (Genesis 18). Open on all four sides.
# ---------------------------------------------------------------------------
for c, r in [(3, 2), (10, 2), (3, 7), (10, 7)]:
    ent("WoodenSupport", c, r, extra=[named("tent pole", "Holds up the corner of a tent that is open on all four sides, so guests can be spotted from any direction.")], blocking=True)
for c in range(5, 9):
    for r in range(3, 7):
        ent("CarpetOrange", c, r)
ent("Bed", 4, 3, blocking=True)
ent("BedsheetBrown", 4, 3)
ent("Bed", 9, 3, extra=[named("Sarah's bed", "Do not laugh near it. She will deny it, but she will hear you.")], blocking=True)
ent("BedsheetBrown", 9, 3)
ent("TableWood", 6, 4, blocking=True)
ent("TableWood", 7, 4, blocking=True)
ent("FoodBreadPlain", 6, 4)
ent("DrinkWaterJug", 7, 4, offset=(-0.2, 0.1))
ent("Paper", 7, 4, offset=(0.15, -0.1), extra=[{
    "type": "Paper",
    "content": "Welcome, traveler!\n\nLet a little water be brought, and wash your feet, and rest yourself under the tree. I will fetch a morsel of bread, and comfort your heart.\n\n(Genesis 18:4-5)\n\nThe tent is open on all four sides. Come in.\n- Abraham",
}])
for c in (6, 7):
    ent("ChairWood", c, 5, R180, blocking=True)
    ent("ChairWood", c, 3, R0, blocking=True)
ent("SpawnPointCanaanAbraham", 8, 6)
ent("Dresser", 4, 6, blocking=True)

# The oaks of Mamre and Abraham's hearth.
for c, r in [(2, 9), (6, 9), (11, 8)]:
    ent("FloraTree", c, r, extra=[named("oak of Mamre", "A great shady tree. Three strangers once rested here and were very well fed.")], blocking=True)
ent("Bonfire", 9, 9, blocking=True)
for c in (8, 10):
    ent("WoodenBench", c, 9, R0, blocking=True)

# ---------------------------------------------------------------------------
# NE: Bethel (Genesis 28), Jacob's kitchen (Genesis 25), the goat pen (Genesis 30)
# ---------------------------------------------------------------------------
ent("FloraRockSolid", 22, 2, extra=[named("pillar of Bethel", "Jacob used this stone as a pillow, dreamed of a ladder to heaven, then set it up as a pillar and poured oil on it. It has been through a lot.")], blocking=True)
ent("NFBedroll", 22, 3)
ent("SpawnPointCanaanJacob", 23, 3)
ent("WoodenSign", 24, 2, extra=[named("sign: Bethel", "\"Surely the LORD is in this place, and I knew it not.\" Mind the angels on the stairs.")])

for c in (27, 28, 29):
    ent("TableCounterWood", c, 1, blocking=True)
ent("FoodSoupStew", 27, 1, extra=[named("red lentil stew", "Smells incredible. Rumor has it someone once traded a birthright for a bowl of this.")])
ent("FoodBowlBig", 28, 1)
ent("FoodBreadPlain", 29, 1)
ent("KitchenElectricRange", 30, 1, blocking=True, power=True)
ent("DrinkKegWood", 31, 2, blocking=True)
ent("ChairWood", 27, 3, R180, blocking=True)
ent("ChairWood", 28, 3, R180, blocking=True)

# Goat pen: fence around the grass at cols 22-30, rows 6-9.
FENCE_L, FENCE_R, FENCE_T, FENCE_B = 21, 31, 5, 10
FENCE_GATE_COL = 26  # one gate on the north side and one on the south side
for c in range(FENCE_L + 1, FENCE_R):
    piece = "FenceWoodSmallGate" if c == FENCE_GATE_COL else "FenceWoodSmallStraight"
    ent(piece, c, FENCE_T, R90, blocking=True)
    ent(piece, c, FENCE_B, R90, blocking=True)
for r in range(FENCE_T + 1, FENCE_B):
    ent("FenceWoodSmallStraight", FENCE_L, r, R0, blocking=True)
    ent("FenceWoodSmallStraight", FENCE_R, r, R0, blocking=True)
ent("FenceWoodSmallCorner", FENCE_L, FENCE_T, R180, blocking=True)   # NW corner: arms south and east
ent("FenceWoodSmallCorner", FENCE_R, FENCE_T, R90, blocking=True)    # NE corner: arms west and south
ent("FenceWoodSmallCorner", FENCE_R, FENCE_B, R0, blocking=True)     # SE corner: arms north and west
ent("FenceWoodSmallCorner", FENCE_L, FENCE_B, R270, blocking=True)   # SW corner: arms east and north
for c, r in [(23, 7), (26, 8), (29, 7)]:
    ent("SpawnMobGoat", c, r)
ent("WoodenSign", 25, 4, extra=[named("sign: Jacob's flocks", "Speckled, spotted, and striped. Jacob is very particular about this.")])

# ---------------------------------------------------------------------------
# Center: the well of Beersheba (Genesis 21, 26)
# ---------------------------------------------------------------------------
for c in (15, 16, 17):
    ent("FloorWaterEntity", c, 10, extra=[named("well of Beersheba", "The well of the oath. Please do not fill it back in with dirt.")])
ent("WoodenSign", 14, 9, extra=[named("sign: Beersheba", "Dug by Abraham, filled in by the Philistines, dug again by Isaac. Please drink responsibly.")])
for c in (14, 18):
    ent("WoodenBench", c, 11, R0, blocking=True)
ent("WarpPoint", 16, 12, extra=[{"type": "WarpPoint", "location": "Canaan"}])

# ---------------------------------------------------------------------------
# SW: Isaac's fields of Gerar (Genesis 26:12) and the well of Rehoboth (26:22)
# ---------------------------------------------------------------------------
for c in (3, 4, 5, 7, 8, 9):
    for r in (17, 20):
        ent("hydroponicsSoil", c, r, blocking=True)
ent("FloorWaterEntity", 11, 16, extra=[named("well of Rehoboth", "\"For now the LORD has made room for us.\" Isaac's third try at a well, and finally nobody argued about it.")])
ent("FloorWaterEntity", 11, 17, extra=[named("well of Rehoboth", "\"For now the LORD has made room for us.\" Isaac's third try at a well, and finally nobody argued about it.")])
ent("WoodenSign", 10, 15, extra=[named("sign: Rehoboth", "Previous wells: Esek (\"contention\") and Sitnah (\"enmity\"). Third time's the charm.")])
ent("Rack", 2, 23, blocking=True)
ent("Shovel", 2, 23, offset=(-0.15, 0.0))
ent("Shovel", 2, 23, offset=(0.15, 0.0))
ent("CrateHydroponicsSeeds", 3, 23, blocking=True)
ent("SeedExtractor", 4, 23, blocking=True, power=True)
ent("Bucket", 5, 23, offset=(-0.15, 0.0))
ent("Bucket", 5, 23, offset=(0.15, 0.0))
ent("HydroponicsToolSpade", 6, 23)
ent("NFBedroll", 11, 22)
ent("SpawnPointCanaanIsaac", 10, 22)

# ---------------------------------------------------------------------------
# SE: the storehouse (power, gravity, air, spare robes)
# ---------------------------------------------------------------------------
SH_L, SH_T = 21, 16  # inner walls on col 21 and row 16; outer wall is the station edge
SH_DOOR = (21, 20)
for c in range(SH_L, W - 1):
    tile(c, SH_T, "Plating")
    walls.add((c, SH_T))
for r in range(SH_T, H - 1):
    tile(SH_L, r, "Plating")
    walls.add((SH_L, r))
for cell in sorted({(c, SH_T) for c in range(SH_L, W - 1)} | {(SH_L, r) for r in range(SH_T + 1, H - 1)}):
    if cell == SH_DOOR:
        continue
    ent("WallSandstone", cell[0], cell[1], blocking=True)
tile(*SH_DOOR, "FloorWood")
ent("WoodDoor", *SH_DOOR, blocking=True)
ent("WoodenSign", 20, 19, extra=[named("sign: storehouse", "Grain, robes, and the machine that keeps your feet on the ground. Like Joseph would have wanted.")])

GEN = (24, 16)    # wall-mounted generator on the storehouse's north wall
SUB = (24, 17)    # substation directly under it
APC = (27, 16)    # wall-mounted APC on the same wall
ent("GeneratorWallmountAPU", *GEN, R0)
ent("SubstationBasic", *SUB, blocking=True)
ent("APCBasic", *APC, R0)
ent("GravityGeneratorMini", 30, 18, blocking=True, power=True)
ent("AirCanister", 31, 23, blocking=True)
ent("AirCanister", 30, 23, blocking=True)
ent("TableWood", 23, 23, blocking=True)
ent("TableWood", 24, 23, blocking=True)
ent("ClothingUniformJumpsuitMonasticRobeLight", 23, 23, offset=(-0.15, 0.1))
ent("ClothingUniformJumpsuitMonasticRobeLight", 23, 23, offset=(0.15, -0.1))
ent("ClothingUniformJumpsuitMonasticRobeDark", 24, 23, offset=(-0.15, 0.1))
ent("ClothingUniformJumpsuitMonasticRobeDark", 24, 23, offset=(0.15, -0.1))
ent("CrateHydroponicsSeeds", 22, 23, blocking=True)
ent("ExtinguisherCabinetFilled", 29, 16, R0)
ent("FireExtinguisher", 22, 18)

# ---------------------------------------------------------------------------
# Lighting: ground light posts in the open, ceiling-free desert style.
# ---------------------------------------------------------------------------
LIGHTS = [(4, 12), (12, 12), (20, 12), (28, 12), (16, 3), (16, 7), (16, 18), (16, 22),
          (2, 4), (12, 4), (24, 4), (8, 15), (26, 19), (29, 21), (6, 21)]
for c, r in LIGHTS:
    ent("PoweredLightPostSmall", c, r, blocking=True, power=True)

# ---------------------------------------------------------------------------
# Power: generator (HV) -> substation (MV) -> APC (LV) -> every powered device
# ---------------------------------------------------------------------------
def neighbors(cell):
    c, r = cell
    for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        n = (c + dc, r + dr)
        if 0 <= n[0] < W and 0 <= n[1] < H:
            yield n


def lay_cable(proto, start, targets, allow_walls):
    """Breadth-first tree from start to each target; returns cells that need cable."""
    prev = {start: None}
    q = deque([start])
    while q:
        cur = q.popleft()
        for n in neighbors(cur):
            if n in prev:
                continue
            if n in walls and not allow_walls and n not in targets:
                continue
            prev[n] = cur
            q.append(n)
    cells = {start}
    for t in targets:
        if t not in prev:
            raise ValueError(f"{proto}: cannot reach {t} from {start}")
        cur = t
        while cur is not None:
            cells.add(cur)
            cur = prev[cur]
    for c, r in sorted(cells):
        ent(proto, c, r)
    return cells


lay_cable("CableHV", GEN, [SUB], allow_walls=True)
mv_cells = lay_cable("CableMV", SUB, [APC], allow_walls=False)
lv_cells = lay_cable("CableApcExtension", APC, powered, allow_walls=False)

# ---------------------------------------------------------------------------
# Checks and preview
# ---------------------------------------------------------------------------
for c, r in tiles:
    assert 0 <= c < W and 0 <= r < H
for proto, c, r, *_ in entities:
    assert (c, r) in tiles, f"{proto} at {(c, r)} has no tile under it"
    assert tiles[(c, r)] != "Space", f"{proto} at {(c, r)} is in space"

spawn_jobs = [p for p, *_ in entities if p.startswith("SpawnPointCanaan")]
assert sorted(spawn_jobs) == ["SpawnPointCanaanAbraham", "SpawnPointCanaanIsaac", "SpawnPointCanaanJacob"], spawn_jobs


def preview():
    glyph = {
        "WallSandstone": "#", "Grille": "W", "AirlockGlassShuttle": "D", "WoodDoor": "d",
        "WoodenSupport": "|", "Bed": "b", "TableWood": "t", "TableCounterWood": "t", "ChairWood": "c",
        "WoodenBench": "n", "FloraTree": "T", "Bonfire": "*", "FloraRockSolid": "R", "Dresser": "x",
        "KitchenElectricRange": "k", "DrinkKegWood": "o", "FenceWoodSmallStraight": "+",
        "FenceWoodSmallGate": "=", "FenceWoodSmallCorner": "+", "hydroponicsSoil": "s", "Rack": "r",
        "CrateHydroponicsSeeds": "C", "SeedExtractor": "e", "GeneratorWallmountAPU": "G",
        "SubstationBasic": "S", "APCBasic": "A", "GravityGeneratorMini": "g", "AirCanister": "a",
        "PoweredLightPostSmall": "L", "SpawnMobGoat": "y", "FloorWaterEntity": "~", "WarpPoint": "@",
        "SpawnPointCanaanAbraham": "1", "SpawnPointCanaanIsaac": "2", "SpawnPointCanaanJacob": "3",
        "WoodenSign": "?",
    }
    base = {"FloorDesert": ".", "FloorLowDesert": ",", "FloorWood": "_", "FloorAstroGrass": "\"", "Plating": "p"}
    grid = [[base[tiles[(c, r)]] for c in range(W)] for r in range(H)]
    for proto, c, r, *_ in entities:
        if proto in glyph:
            grid[r][c] = glyph[proto]
    return "\n".join("".join(row) for row in grid)


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------
CHUNK = 16


def encode_chunks():
    chunks = {}
    for (c, r), name in tiles.items():
        x, y = to_world(c, r)
        cx, cy = math.floor(x / CHUNK), math.floor(y / CHUNK)
        chunks.setdefault((cx, cy), {})[(x - cx * CHUNK, y - cy * CHUNK)] = name
    out = {}
    for key, cells in chunks.items():
        buf = bytearray()
        for ly in range(CHUNK):
            for lx in range(CHUNK):
                name = cells.get((lx, ly), "Space")
                tid = TILEMAP[name]
                # Deterministic variant spread so floors don't look stamped.
                gx, gy = key[0] * CHUNK + lx, key[1] * CHUNK + ly
                variant = 0 if name == "Space" else ((gx * 7 + gy * 13) % TILE_VARIANTS[name])
                buf += struct.pack("<iBBB", tid, 0, variant, 0)
        out[key] = base64.b64encode(bytes(buf)).decode()
    return out


def encode_atmos():
    """Standard air on every walkable tile. Walls and space get none."""
    chunks = {}
    for (c, r), name in tiles.items():
        if name == "Space" or ((c, r) in walls and (c, r) not in dock_cells and (c, r) != SH_DOOR):
            continue
        x, y = to_world(c, r)
        key = (math.floor(x / 4), math.floor(y / 4))
        lx, ly = x - key[0] * 4, y - key[1] * 4
        chunks[key] = chunks.get(key, 0) | (1 << (lx + ly * 4))
    return chunks


def fmt_rot(rot):
    if rot == 0:
        return None
    return f"{rot!r} rad"


def fmt_pos(c, r, offset):
    x, y = to_world(c, r)
    px, py = x + 0.5 + offset[0], y + 0.5 + offset[1]

    def f(v):
        v = round(v, 6)
        return str(int(v)) if v == int(v) else repr(v)
    return f"{f(px)},{f(py)}"


def yaml_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def emit_component(lines, comp, indent="    "):
    comp = dict(comp)
    lines.append(f"{indent}- type: {comp.pop('type')}")
    for k, v in comp.items():
        lines.append(f"{indent}  {k}: {yaml_str(v) if isinstance(v, str) else v}")


def write():
    GRID_UID = 1
    by_proto = {}
    uid = GRID_UID + 1
    for proto, c, r, rot, extra, offset in entities:
        by_proto.setdefault(proto, []).append((uid, c, r, rot, extra, offset))
        uid += 1
    entity_count = uid - 1

    lines = [
        "meta:",
        "  format: 7",
        "  category: Grid",
        "  engineVersion: 267.3.0",
        '  forkId: ""',
        '  forkVersion: ""',
        "  time: 10/12/2026 23:00:00",
        f"  entityCount: {entity_count}",
        "maps: []",
        "grids:",
        f"- {GRID_UID}",
        "orphans:",
        f"- {GRID_UID}",
        "nullspace: []",
        "tilemap:",
    ]
    for name, tid in sorted(TILEMAP.items(), key=lambda kv: kv[1]):
        lines.append(f"  {tid}: {name}")
    lines += [
        "entities:",
        '- proto: ""',
        "  entities:",
        f"  - uid: {GRID_UID}",
        "    components:",
        "    - type: MetaData",
        "      name: Canaan",
        "    - type: Transform",
        "      parent: invalid",
        "    - type: MapGrid",
        "      chunks:",
    ]
    for (cx, cy), data in sorted(encode_chunks().items()):
        lines += [
            f"        {cx},{cy}:",
            f"          ind: {cx},{cy}",
            f"          tiles: {data}",
            "          version: 7",
        ]
    lines += [
        "    - type: Broadphase",
        "    - type: Physics",
        "      bodyStatus: InAir",
        "      angularDamping: 0.05",
        "      linearDamping: 0.05",
        "      fixedRotation: False",
        "      bodyType: Dynamic",
        "    - type: Fixtures",
        "      fixtures: {}",
        "    - type: OccluderTree",
        "    - type: SpreaderGrid",
        "    - type: Shuttle",
        "      dampingModifier: 0.25",
        "    - type: GridPathfinding",
        "    - type: BecomesStation",
        "      id: Canaan",
        "    - type: Gravity",
        "      gravityShakeSound: !type:SoundPathSpecifier",
        "        path: /Audio/Effects/alert.ogg",
        "    - type: DecalGrid",
        "      chunkCollection:",
        "        version: 2",
        "        nodes: []",
        "    - type: GridAtmosphere",
        "      version: 2",
        "      data:",
        "        tiles:",
    ]
    for (cx, cy), mask in sorted(encode_atmos().items()):
        lines += [f"          {cx},{cy}:", f"            0: {mask}"]
    lines += [
        "        uniqueMixes:",
        "        - volume: 2500",
        "          temperature: 293.15",
        "          moles:",
        "          - 21.824879",
        "          - 82.10312",
    ] + ["          - 0"] * 10 + [
        "        chunkSize: 4",
        "    - type: GasTileOverlay",
        "    - type: RadiationGridResistance",
        "    - type: ImplicitRoof",
    ]
    for proto in sorted(by_proto, key=lambda p: p.lower()):
        lines += [f"- proto: {proto}", "  entities:"]
        for uid, c, r, rot, extra, offset in by_proto[proto]:
            lines += [f"  - uid: {uid}", "    components:"]
            meta = [e for e in extra if e["type"] == "MetaData"]
            for m in meta:
                emit_component(lines, m)
            lines.append("    - type: Transform")
            if fmt_rot(rot):
                lines.append(f"      rot: {fmt_rot(rot)}")
            lines.append(f"      pos: {fmt_pos(c, r, offset)}")
            lines.append(f"      parent: {GRID_UID}")
            for e in extra:
                if e["type"] != "MetaData":
                    emit_component(lines, e)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return entity_count


if __name__ == "__main__":
    print(preview())
    n = write()
    print(f"\nWrote {OUT.relative_to(ROOT)}: {n} entities, {len(tiles)} tiles, "
          f"{len(powered)} powered devices, {len(lv_cells)} LV cable tiles")
