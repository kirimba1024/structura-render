"""Copy compact input examples; render their outputs only when requested."""

import argparse
from importlib.resources import files
from pathlib import Path

from .export_io import atomic_write


def copy_examples(directory, *, showcase=False):
    directory = Path(directory).expanduser().resolve()
    names = ['demo.nbt', 'README.md']
    if showcase:
        names += ['blocks.nbt', 'entities.nbt', 'coverage.json']
    bundled = files(__package__).joinpath('data').joinpath('examples')
    contents = {directory / name: bundled.joinpath(name).read_bytes() for name in names}
    for path, data in contents.items():
        if path.exists() and (not path.is_file() or path.read_bytes() != data):
            raise FileExistsError(f'example output already exists with different content: {path}')
    for path, data in contents.items():
        if not path.exists():
            atomic_write(path, data)
    return list(contents)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', nargs='?', default='structura-examples')
    parser.add_argument('--showcase', action='store_true', help='include the block and entity catalogs')
    args = parser.parse_args(argv)
    try:
        for path in copy_examples(args.directory, showcase=args.showcase):
            print(path)
    except OSError as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
