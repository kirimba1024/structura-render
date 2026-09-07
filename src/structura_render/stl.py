from .export_io import atomic_write


def export_stl(parts, output):
    """Export a single oriented surface; no artificial back-face duplication."""
    import trimesh

    if not parts:
        raise ValueError("structure produced no visible geometry")
    combined = trimesh.util.concatenate([part for _, part in parts])
    # Welding removes per-face UV seams, which STL cannot represent. Coincident
    # triangles (including reverse sides of sprites) are one geometric surface.
    combined.visual = trimesh.visual.ColorVisuals()
    combined.merge_vertices()
    combined.update_faces(combined.unique_faces())
    atomic_write(output, combined.export(file_type="stl"))
    return combined


def main(argv=None):
    from .export import export_cli

    export_cli("stl", argv)


if __name__ == "__main__":
    main()
