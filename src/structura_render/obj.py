import re

from .export_io import write_obj as write_obj

def add_alpha_maps(obj_path):
    obj_text = obj_path.read_text()
    mtllib = re.search(r"^mtllib (.+)$", obj_text, re.MULTILINE)
    if not mtllib:
        return
    mtl_path = obj_path.parent / mtllib.group(1)
    mtl_text = mtl_path.read_text()
    mtl_text = re.sub(
        r"^(map_Kd (.+))$", r"\1\nmap_d \2", mtl_text, flags=re.MULTILINE,
    )
    mtl_path.write_text(mtl_text)


def main(argv=None):
    from .export import export_cli

    export_cli("obj", argv)


if __name__ == "__main__":
    main()
