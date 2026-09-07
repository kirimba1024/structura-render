from .export_io import write_gltf as write_gltf


def main(argv=None):
    from .export import export_cli

    export_cli("gltf", argv)


if __name__ == "__main__":
    main()
