import numpy as np

from .assets import current_context
from .atlas import (
    ATLAS_UPSCALE as ATLAS_UPSCALE,
    FACE_UV_AXES as FACE_UV_AXES,
    MAX_ATLAS_SIZE as MAX_ATLAS_SIZE,
    Atlas as Atlas,
    atlas_uv as atlas_uv,
    cropped_uv as cropped_uv,
    face_texture_key as face_texture_key,
    face_uv as face_uv,
    map_uv,
    upscale_atlas as upscale_atlas,
    uv_for_rect as uv_for_rect,
    uv_pixel_bounds as uv_pixel_bounds,
    uv_points_for_rect as uv_points_for_rect,
)
from .block_geometry import (
    ARM_AXIS as ARM_AXIS,
    ARM_SIDE_FACES as ARM_SIDE_FACES,
    ARM_SPAN as ARM_SPAN,
    CROSS_PLANES as CROSS_PLANES,
    FENCE_BAR_THICKNESS as FENCE_BAR_THICKNESS,
    FENCE_BAR_Y as FENCE_BAR_Y,
    FENCE_POST as FENCE_POST,
    FLOWER_NAMES as FLOWER_NAMES,
    GLASS_ALPHA as GLASS_ALPHA,
    PANE_POST as PANE_POST,
    PANE_THICKNESS as PANE_THICKNESS,
    TORCH_STANDING as TORCH_STANDING,
    TORCH_WALL as TORCH_WALL,
    WALL_LOW_TOP as WALL_LOW_TOP,
    WALL_POST as WALL_POST,
    WALL_THICKNESS as WALL_THICKNESS,
    WALL_TORCH_OFFSET as WALL_TORCH_OFFSET,
    arm_bounds as arm_bounds,
    block_masks,
    emit_fallback_blocks,
    flat_block_groups as flat_block_groups,
    flat_rgba as flat_rgba,
    is_bars as is_bars,
    is_cross as is_cross,
    is_fence as is_fence,
    is_fence_gate as is_fence_gate,
    is_occluder as is_occluder,
    is_pane as is_pane,
    is_post_family as is_post_family,
    is_wall as is_wall,
    normalize_legacy as normalize_legacy,
    torch_boxes as torch_boxes,
    voxel_state as voxel_state,
)
from .diagnostics import render_diagnostics
from .entities import structure_parts
from .entity_shapes import INVISIBLE
from .geometry import (
    ALPHA_MODES as ALPHA_MODES,
    CUBE_CORNERS as CUBE_CORNERS,
    CUBE_FACES as CUBE_FACES,
    DEFAULT_MAX_ATLAS_SIZE,
    DEFAULT_MAX_VOXELS,
    FACE_STEP as FACE_STEP,
    FlatMesh,
    UV_CORNERS as UV_CORNERS,
    SceneGeometry,
    TexturedMesh,
    alpha_mode as alpha_mode,
    box_corners as box_corners,
    connects_mask as connects_mask,
    double_sided_triangles as double_sided_triangles,
    exposed_mask as exposed_mask,
    exposed_positions,
    mask_surface as mask_surface,
    material_groups as material_groups,
    quads_from_positions as quads_from_positions,
    rotate_y as rotate_y,
    shift_toward as shift_toward,
    triangulate_quads as triangulate_quads,
    vtk_quads as vtk_quads,
)
from .mesh_models import (
    instance_groups as instance_groups,
    prepare_models,
    resolve_special_parts as resolve_special_parts,
)


class QuadBuffer:
    def __init__(self, atlas_image, rects, emit_bounds=None, emit_mask=None):
        self.atlas_image = atlas_image
        self.rects = rects
        self.points_all = []
        self.faces_all = []
        self.uv_all = []
        self.material_modes = []
        self.mode_cache = {}
        self.vertex_count = 0
        self.emit_bounds = emit_bounds
        self.emit_mask = emit_mask

    def append(self, positions, offsets, uv):
        if self.emit_bounds is not None:
            lower, upper = self.emit_bounds
            positions = positions[((positions >= lower) & (positions < upper)).all(axis=1)]
        if self.emit_mask is not None and len(positions):
            positions = positions[self.emit_mask[tuple(positions.astype(np.intp).T)]]
        if len(positions) == 0:
            return
        points = (positions[:, None, :] + offsets[None, :, :]).reshape(-1, 3)
        faces = np.arange(self.vertex_count, self.vertex_count + len(points)).reshape(-1, 4)
        self.vertex_count += len(points)
        self.points_all.append(points)
        self.faces_all.append(faces)
        self.uv_all.append(np.tile(uv, (len(positions), 1)))
        bounds = uv_pixel_bounds(self.atlas_image, uv)
        if bounds not in self.mode_cache:
            x0, y0, x1, y1 = bounds
            self.mode_cache[bounds] = ALPHA_MODES.index(alpha_mode(self.atlas_image[y0:y1, x0:x1]))
        self.material_modes.append(np.full(len(points) // 4, self.mode_cache[bounds], dtype=np.uint8))

    def meshes(self):
        if not self.points_all:
            return []
        if self.atlas_image is None:
            raise RuntimeError("textured geometry was built without an atlas")
        return [TexturedMesh(
            np.vstack(self.points_all), np.vstack(self.faces_all),
            np.vstack(self.uv_all), np.concatenate(self.material_modes), self.atlas_image,
        )]


def _emit_models(blocks, state, names, occluder, buffer):
    from .block_geometry import LEAF_INTERIOR_FACES, surface_neighbors

    for index, faces in blocks.items():
        own = state == index
        if not own.any():
            continue
        neighbors = surface_neighbors(state, index, names, occluder, own)
        for face in faces:
            solid = occluder if names[index].endswith("_leaves") and face.cullface in LEAF_INTERIOR_FACES else neighbors
            mask = exposed_mask(own, solid, face.cullface) if face.cullface else own
            pos = np.argwhere(mask).astype(np.float32)
            uv = map_uv(buffer.rects[face.rect_index], face.uv)
            buffer.append(pos, face.vertices, uv)


def _emit_specials(models, index_names, masks, buffer):
    own = np.zeros_like(masks.occluder)
    for model in models.specials:
        own[tuple(model.positions.T)] = True
        name = model.fluid or index_names[model.index]
        neighbors = (masks.water if name in ("minecraft:water", "minecraft:bubble_column") else
                     masks.lava if name == "minecraft:lava" else own)
        for part in model.parts:
            lo, hi = part["lo"], part["hi"]
            raw_corners = np.asarray(part.get("corners", box_corners(lo, hi)), dtype=np.float32)
            corners = rotate_y(raw_corners, part["angle"])
            for direction, indices in CUBE_FACES.items():
                axis = next(i for i, value in enumerate(FACE_STEP[direction]) if value)
                edge = lo[axis] == 0 if FACE_STEP[direction][axis] < 0 else hi[axis] == 1
                positions = model.positions
                if edge and part["angle"] % 90 == 0:
                    positions = exposed_positions(positions, direction, masks.occluder, neighbors)
                if "rect_by_face" in part:
                    if direction not in part["rect_by_face"]:
                        continue
                    rect_index = part["rect_by_face"][direction]
                else:
                    rect_index = part["rect_index"]
                buffer.append(positions.astype(np.float32), corners[indices], face_uv(uv_for_rect(buffer.rects[rect_index]), direction))
        own[tuple(model.positions.T)] = False


def _emit_entities(parts, buffer):
    for anchor, part in parts:
        origin = np.array([anchor], dtype=np.float32)
        pivot = part.get("pivot", (0.5, 0.5))
        angle = part.get("angle", 0)
        if "quads" in part:
            rect = buffer.rects[part["rect_index"]]
            mapped_uv = part.get("quad_uvs")
            for index, quad in enumerate(part["quads"]):
                uv = (
                    uv_points_for_rect(rect, mapped_uv[index])
                    if mapped_uv else uv_for_rect(rect)
                )
                vertices = rotate_y(np.asarray(quad, dtype=np.float32), angle, pivot)
                buffer.append(origin, vertices, uv)
            continue
        corners = rotate_y(box_corners(part["lo"], part["hi"]), angle, pivot)
        directions = part.get("only_faces") or CUBE_FACES
        for direction in directions:
            if "rect_by_face" in part:
                if direction not in part["rect_by_face"]:
                    continue
                rect_index = part["rect_by_face"][direction]
            else:
                rect_index = part["rect_index"]
            buffer.append(origin, corners[CUBE_FACES[direction]], face_uv(uv_for_rect(buffer.rects[rect_index]), direction))


def build_textured_geometry(src, solid, state, index_names, index_props, bank, *, max_atlas_size=DEFAULT_MAX_ATLAS_SIZE, strict=False, emit_bounds=None, emit_mask=None):
    context = getattr(bank, "context", None) or current_context()
    with render_diagnostics(strict=strict), context.activate():
        return _build_textured_geometry(src, solid, state, index_names, index_props, bank,
                                        max_atlas_size=max_atlas_size, emit_bounds=emit_bounds, emit_mask=emit_mask)


def _build_textured_geometry(src, solid, state, index_names, index_props, bank, *, max_atlas_size, emit_bounds, emit_mask):
    atlas = Atlas(max_size=max_atlas_size)
    models = prepare_models(src, state, index_names, index_props, bank, atlas)
    masks = block_masks(state, index_names, index_props)
    image, rects = atlas.build(max_size=max_atlas_size) if atlas.images else (None, [])
    buffer = QuadBuffer(image, rects, emit_bounds, emit_mask)
    _emit_models(models.blocks, state, index_names, masks.occluder, buffer)
    _emit_specials(models, index_names, masks, buffer)
    emit_fallback_blocks(models.fallback, state, index_names, index_props, masks, buffer)
    _emit_entities(models.entities, buffer)
    return buffer.meshes(), [], models.textured_indices, masks.occluder


def build_textured_meshes(src, solid, state, index_names, index_props, bank, *, max_atlas_size=DEFAULT_MAX_ATLAS_SIZE, strict=False):
    """Compatibility adapter returning PyVista meshes and textures."""
    meshes, entities, indices, occluder = build_textured_geometry(
        src, solid, state, index_names, index_props, bank, max_atlas_size=max_atlas_size, strict=strict,
    )
    return [mesh.to_pyvista() for mesh in meshes], entities, indices, occluder


def double_sided_trimesh(points, tris, visual=None):
    import trimesh

    return trimesh.Trimesh(
        vertices=points, faces=double_sided_triangles(tris), visual=visual, process=False,
    )


def export_parts(meshes, flat_groups, center):
    """Compatibility entry point; trimesh is loaded only for its exporters."""
    from .mesh_export import export_parts as export

    return export(meshes, flat_groups, center)


def structure_export_parts(src, bank, *, max_voxels=DEFAULT_MAX_VOXELS, max_atlas_size=DEFAULT_MAX_ATLAS_SIZE, strict=False):
    scene = build_scene_geometry(
        src, bank, max_voxels=max_voxels, max_atlas_size=max_atlas_size, strict=strict,
    )
    center = np.asarray(src.size, dtype=np.float32) / 2.0
    return export_parts(scene.meshes, scene.flat_groups, center)


def build_scene_geometry(src, bank=None, *, color_mode="family", max_voxels=DEFAULT_MAX_VOXELS,
                         max_atlas_size=DEFAULT_MAX_ATLAS_SIZE, strict=False):
    if color_mode not in {"family", "block"}:
        raise ValueError("color_mode must be 'family' or 'block'")
    state, solid, names, props = voxel_state(src, max_voxels=max_voxels)
    if bank is None:
        hidden = {index for index, name in names.items() if name in INVISIBLE}
        groups = flat_block_groups(state, names, hidden, np.zeros_like(solid), color_mode=color_mode)
        if src.entities:
            with render_diagnostics(strict=strict), current_context().activate():
                groups.extend(flat_entity_groups(src))
        return SceneGeometry([], groups)
    meshes, _, indices, occluder = build_textured_geometry(
        src, solid, state, names, props, bank, max_atlas_size=max_atlas_size, strict=strict,
    )
    groups = flat_block_groups(state, names, indices, occluder, color_mode=color_mode)
    return SceneGeometry(meshes, groups)


def flat_entity_groups(source):
    groups = {}
    for anchor, parts in structure_parts(source):
        for part in parts:
            quads = part.get("quads")
            if quads is None:
                corners = np.asarray(part.get("corners", box_corners(part["lo"], part["hi"])), dtype=np.float32)
                directions = part.get("only_faces") or part.get("faces") or CUBE_FACES
                quads = [corners[CUBE_FACES[face]] for face in directions]
            points = np.asarray(quads, dtype=np.float32).reshape(-1, 3)
            points = rotate_y(points, part.get("angle", 0), part.get("pivot", (0.5, 0.5))) + anchor
            color = (*(part.get("tint") or (180, 185, 190)), part.get("alpha", 255))
            groups.setdefault(color, []).append(points)
    result = []
    for color, parts in groups.items():
        points = np.concatenate(parts)
        if len(points):
            result.append(FlatMesh(color, points, np.arange(len(points)).reshape(-1, 4)))
    return result
