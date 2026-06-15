import bpy

from os import path
from typing import List, Set, Tuple

from .util import pack_empty_png, aseprite_pixels_to_image, image_pixels_set


def layer_images(sprite_name:str) -> List[bpy.types.Image]:
    source = bpy.path.abspath(sprite_name) if sprite_name.startswith("//") else sprite_name
    source = path.normpath(source)
    return [
        image for image in bpy.data.images
        if image.sb_props.is_layer
        and path.normpath(image.sb_props.source_abs) == source
    ]


def legacy_tree(sprite_name:str) -> bpy.types.ShaderNodeTree:
    source = bpy.path.abspath(sprite_name) if sprite_name.startswith("//") else sprite_name
    source = path.normpath(source)
    return next((
        tree for tree in bpy.data.node_groups
        if tree.type == 'SHADER'
        and hasattr(tree, "sb_props")
        and path.normpath(tree.sb_props.source_abs) == source
    ), None)


def update_layer_images(sprite_name:str, sprite_width:int, sprite_height:int,
        flags:Set[str], groups:List[Tuple], layers:List[Tuple]) -> List[bpy.types.Image]:
    """Update separate Blender Images without creating a compositing node group."""
    basename = bpy.path.basename(sprite_name)
    owners = layer_images(sprite_name)
    existing = {
        image.sb_props.layer_index: image
        for image in owners
        if not image.sb_props.is_layer_placeholder
    }
    legacy = legacy_tree(sprite_name)
    stored_source = next((
        image.sb_props.source for image in owners
        if image.sb_props.source
    ), legacy.sb_props.source if legacy else sprite_name)
    legacy_images = set()
    if legacy:
        legacy_images = {
            node.image for node in legacy.nodes
            if node.type == 'TEX_IMAGE' and node.image
        }

    updated = []
    used = set()

    if not layers:
        image = owners[0] if owners else bpy.data.images.new(basename, 1, 1, alpha=True)
        if not owners:
            image.sb_props.needs_save = True
            pack_empty_png(image)
        image.sb_props.source = stored_source
        image.sb_props.sync_flags = flags
        image.sb_props.is_layer = True
        image.sb_props.is_layer_placeholder = True
        image.sb_props.layer_index = -1
        image.sb_props.layer_name = ""
        image.sb_props.layer_group = ""
        image.sb_props.layer_blend = 0
        image.sb_props.layer_opacity = 0
        image.sb_props.layer_bounds = (0, 0, 0, 0)
        image.sb_props.sprite_size = (sprite_width, sprite_height)
        if image.size != (1, 1):
            image.scale(1, 1)
        image_pixels_set(image, [0.0, 0.0, 0.0, 0.0])
        image.update()
        image.update_tag()
        return [image]

    for idx, blend, opacity, group, x, y, w, h, name, pixels in layers:
        image = existing.get(idx)
        expected_name = f"{basename}:{name}"

        if image is None:
            image = next((
                candidate for candidate in legacy_images
                if candidate.name == expected_name
            ), None)

        if image is None:
            image = bpy.data.images.new(expected_name, max(1, w), max(1, h), alpha=True)
            image.sb_props.needs_save = True
            pack_empty_png(image)

        image.name = expected_name
        image.sb_props.source = stored_source
        image.sb_props.sync_flags = flags
        image.sb_props.is_layer = True
        image.sb_props.is_layer_placeholder = False
        image.sb_props.layer_index = idx
        image.sb_props.layer_name = name
        image.sb_props.layer_group = groups[group - 1][0] if group else ""
        image.sb_props.layer_blend = blend.value
        image.sb_props.layer_opacity = opacity
        image.sb_props.layer_bounds = (x, y, w, h)
        image.sb_props.sprite_size = (sprite_width, sprite_height)

        if pixels:
            if image.size != (w, h):
                image.scale(w, h)
            image_pixels_set(
                image,
                aseprite_pixels_to_image(image, pixels, (w, h)))
        else:
            if image.size != (1, 1):
                image.scale(1, 1)
            image_pixels_set(image, [0.0, 0.0, 0.0, 0.0])

        image.update()
        image.update_tag()
        updated.append(image)
        used.add(image)

    for image in layer_images(sprite_name):
        if image not in used:
            bpy.data.images.remove(image)

    return updated
