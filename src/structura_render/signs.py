import json
import math

from . import font
from .block_colours import DYES
from .shape_geometry import HALF_TURN_X, HALF_TURN_Z, _px, angle_for, box, cube_faces, unwrap


def _plain_text(component):
    """A text component flattened to the characters it actually shows.

    A component is a tree: its own `text` followed by its `extra` children,
    each of which is another component. Reading only the root's `text` renders
    a sign as blank whenever an editor wrote the line as a list or wrapped it
    in a formatting child, which is common and gives no hint that anything
    was lost.
    """
    if isinstance(component, str):
        return component
    if isinstance(component, list):
        return "".join(_plain_text(child) for child in component)
    if isinstance(component, dict):
        return str(component.get("text", "")) + "".join(
            _plain_text(child) for child in component.get("extra", [])
        )
    return ""


def _sign_side(component):
    lines = []
    for raw in component.get("messages", []):
        raw = str(raw)
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = raw
        lines.append(_plain_text(parsed))
    if not any(lines):
        return None
    color = str(component.get("color", "black"))
    return (tuple(lines), color if color in DYES else "black", bool(component.get("has_glowing_text", 0)))


SIGN_LINES = 4

TEXT_DEPTH = 0.08 / 16


def sign_text_metrics(base):
    """Blocks per text pixel, pixels between lines, and the widest line the
    board takes. A hanging sign writes bigger letters on a smaller board, so
    it fits fewer of them: the game's own numbers, not a scaled guess.
    """
    if "hanging_sign" in base:
        return 0.9 / 64, 9, 60
    return 1 / 96, 10, 90


def _text_line_boxes(lines, board_lo, board_hi, face_z, direction, tint, angle, metrics):
    scale, line_height, max_width = metrics
    band = line_height * scale
    middle_x = (board_lo[0] + board_hi[0]) / 2
    middle_y = (board_lo[1] + board_hi[1]) / 2
    z0, z1 = (face_z, face_z + TEXT_DEPTH) if direction > 0 else (face_z - TEXT_DEPTH, face_z)
    outward = "south" if direction > 0 else "north"
    boxes = []
    for row, line in enumerate(lines[:SIGN_LINES]):
        glyphs = [font.glyph(char) for char in line]
        width = sum(advance for _, _, advance in glyphs) - 1 if glyphs else 0

        line_scale = scale * min(1, max_width / width) if width > 0 else scale
        top = middle_y + (SIGN_LINES / 2 - row) * band
        bottom = top - font.HEIGHT * line_scale
        cursor = middle_x - direction * width * line_scale / 2
        for texture, crop, advance in glyphs:
            if texture is not None:
                edge = cursor + direction * (advance - 1) * line_scale
                boxes.append(box(
                    (min(cursor, edge), bottom, z0), (max(cursor, edge), top, z1),
                    texture, tint=tint, angle=angle, faces={outward: crop},
                ))
            cursor += direction * advance * line_scale
    return boxes


def sign_text_boxes(content, board_lo, board_hi, angle, back, wall, metrics):
    """The text on one or both sides of a board.

    A standing board sits in the middle of its block and is read from the
    high-z side; a wall board is pushed back against the block it hangs on,
    so it is read from the low-z one. Reading the front off the wrong face
    puts the text inside the wall, which looks like no text at all rather
    than like a mistake.
    """
    sides = [("front_text", board_lo[2], -1)] if wall else [("front_text", board_hi[2], 1)]
    if back:
        sides.append(("back_text", board_lo[2], -1))
    boxes = []
    for side, face_z, direction in sides:
        parsed = content.get(side)
        if not parsed:
            continue
        lines, color, _glow = parsed
        boxes.extend(_text_line_boxes(lines, board_lo, board_hi, face_z, direction,
                                      DYES[color], angle, metrics))
    return boxes


def sign_board_bounds(base):
    """The board's own box, and the pose its model is set in.

    A sign has no block model -- the game draws it as an entity whose
    geometry lives in code -- so these come from that code. A standing
    board is the full width of its block and stands proud of the top; a
    wall board is pushed back against the block it hangs on, which at yaw 0
    means the far side, not the near one.
    """
    wall = "_wall_" in base
    if "hanging_sign" in base:
        return (1 / 16, 0, 7 / 16), (15 / 16, 10 / 16, 9 / 16), wall, HALF_TURN_X

    lo = (0, 0.5 + _px(2), 0.5 - _px(1))
    hi = (1, 0.5 + _px(14), 0.5 + _px(1))
    if wall:
        lo = (lo[0], lo[1] - 5 / 16, lo[2] + 7 / 16)
        hi = (hi[0], hi[1] - 5 / 16, hi[2] + 7 / 16)
    return lo, hi, wall, HALF_TURN_Z if wall else HALF_TURN_X


def _hanging_plane(texture, offset, origin, size, pivot, local_angle, angle):
    radians = math.radians(local_angle)
    cosine, sine = math.cos(radians), math.sin(radians)
    x, y, z = origin
    width, height, depth = size
    corners = []
    for px, py, pz in (
        (x, y, z), (x + width, y, z), (x + width, y, z + depth), (x, y, z + depth),
        (x, y + height, z), (x + width, y + height, z),
        (x + width, y + height, z + depth), (x, y + height, z + depth),
    ):
        turned_x = px * cosine + pz * sine + pivot[0]
        turned_z = -px * sine + pz * cosine + pivot[2]
        model_y = py + pivot[1]
        corners.append((.5 + turned_x / 16, .625 - model_y / 16,
                        .5 - turned_z / 16))
    lo = tuple(min(point[i] for point in corners) for i in range(3))
    hi = tuple(max(point[i] for point in corners) for i in range(3))
    crops = cube_faces(offset, size)
    part = box(lo, hi, texture, angle=angle,
               faces={face: crops[face] for face in ("north", "south")})
    part["corners"] = corners
    return part


def sign(base, props, content=None):
    hanging = "hanging_sign" in base
    wood = base.split("_wall", 1)[0].split("_hanging", 1)[0].removesuffix("_sign")
    texture = f"entity/signs/{'hanging/' if hanging else ''}{wood}"
    angle = angle_for(props)
    board_lo, board_hi, wall, pose = sign_board_bounds(base)
    board_size = (14, 10, 2) if hanging else (24, 12, 2)
    board_offset = (0, 12) if hanging else (0, 0)
    result = [box(board_lo, board_hi, texture, angle=angle,
                  **unwrap(board_offset, board_size, pose))]
    if hanging:
        ceiling = "_wall_" not in base
        if not ceiling:
            result.append(box((0, 14 / 16, 6 / 16), (1, 1, 10 / 16), texture,
                              angle=angle, **unwrap((0, 0), (16, 2, 4), HALF_TURN_X)))
        if ceiling and props.get("attached") == "true":
            result.append(_hanging_plane(
                texture, (14, 6), (-6, -6, 0), (12, 6, 0), (0, 0, 0), 0, angle,
            ))
        else:
            segments = (
                ((0, 6), (-5, -6, 0), -45), ((6, 6), (-5, -6, 0), 45),
                ((0, 6), (5, -6, 0), -45), ((6, 6), (5, -6, 0), 45),
            )
            result.extend(_hanging_plane(
                texture, offset, (-1.5, 0, 0), (3, 6, 0), pivot, turn, angle,
            ) for offset, pivot, turn in segments)
    elif not wall:
        stick = _px(1)
        result.append(box(
            (0.5 - stick, 0, 0.5 - stick), (0.5 + stick, board_lo[1], 0.5 + stick),
            texture, angle=angle, **unwrap((0, 14), (2, 14, 2), pose),
        ))
    if content:
        result.extend(sign_text_boxes(content, board_lo, board_hi, angle,
                                      not wall, wall, sign_text_metrics(base)))
    return result


def entity_decoration(name, props, content):
    base = name.split(":", 1)[-1]
    if base.endswith(("_sign", "_hanging_sign")):
        sides = content[1] if content and content[0] == "sign" else None
        if not sides:
            return []
        board_lo, board_hi, wall, _pose = sign_board_bounds(base)
        return sign_text_boxes(dict(sides), board_lo, board_hi, angle_for(props),
                               not wall, wall, sign_text_metrics(base))
    return []
