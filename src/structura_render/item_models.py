"""Resolve a representative texture for an item stack from client assets.

Items gained a top-level ``items/<id>.json`` dispatch layer in newer packs,
while 1.21.1 and older packs start directly at ``models/item/<id>.json``.
The renderer only needs the base, static appearance here: enough to put a
recognisable item in a frame, an armor-stand slot, or an item entity without
reimplementing the client's predicates, glints, trims, or animation.
"""

import json

from .assets import context_cached, current_context


def _plain(value):
    return str(value).split(":", 1)[-1]


def item_id(stack):
    """Return a namespaced stack id, or ``None`` for an empty/malformed slot."""
    if not stack or not hasattr(stack, "get"):
        return None
    raw = stack.get("id") or stack.get("Id")
    if raw is None:
        return None
    count = stack.get("count", stack.get("Count", 1))
    try:
        if int(str(count)) <= 0:
            return None
    except ValueError:
        return None
    name = str(raw)
    return name if ":" in name else f"minecraft:{name}"


@context_cached
def _json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _static_model(node):
    """Pick the non-conditional model from a modern item definition.

    Dynamic dispatch depends on world/entity state that a saved structure
    does not carry. Its explicit fallback is therefore the truthful static
    choice; simple model and composite nodes are common and deterministic.
    """
    if not isinstance(node, dict):
        return None
    kind = _plain(node.get("type", ""))
    if kind == "model":
        return node.get("model")
    if kind == "composite":
        for child in node.get("models", ()):
            selected = _static_model(child)
            if selected:
                return selected
        return None
    fallback = node.get("fallback") or node.get("on_false") or node.get("on_true")
    selected = _static_model(fallback)
    if selected:
        return selected
    for key in ("cases", "entries"):
        for entry in node.get(key, ()):
            selected = _static_model(entry.get("model", entry) if hasattr(entry, "get") else entry)
            if selected:
                return selected
    return None


def _model_path(name):
    return current_context().path("models", name, ".json")


@context_cached
def _resolved_model(name, depth=0):
    if depth > 16:
        return None
    data = _json(_model_path(name))
    if data is None:
        return None
    parent = data.get("parent")
    base = _resolved_model(str(parent), depth + 1) if parent else {"textures": {}}
    if base is None:
        base = {"textures": {}}
    return {"textures": {**base.get("textures", {}), **data.get("textures", {})}}


def _texture_ref(ref, textures, depth=0):
    if ref is None or depth > 16:
        return None
    if isinstance(ref, dict):
        return _texture_ref(ref.get("sprite"), textures, depth + 1)
    ref = str(ref)
    if ref.startswith("#"):
        return _texture_ref(textures.get(ref[1:]), textures, depth + 1)
    return _plain(ref)


@context_cached
def item_texture(identifier):
    """Return a texture stem for the stack's base static item appearance."""
    name = _plain(identifier)
    definition = _json(current_context().path("items", identifier, ".json"))
    model_name = _static_model(definition.get("model")) if definition else None
    model_name = model_name or f"item/{name}"
    model = _resolved_model(str(model_name))
    if model is None:
        direct = f"item/{name}"
        return direct if (current_context().path("textures", direct, ".png")).is_file() else None
    textures = model["textures"]
    for key in ("layer0", "particle", "all", "texture", "side", "top"):
        stem = _texture_ref(textures.get(key), textures)
        if stem and (current_context().path("textures", stem, ".png")).is_file():
            return stem
    for ref in textures.values():
        stem = _texture_ref(ref, textures)
        if stem and (current_context().path("textures", stem, ".png")).is_file():
            return stem
    return None


def stack_texture(stack):
    identifier = item_id(stack)
    return item_texture(identifier) if identifier else None
