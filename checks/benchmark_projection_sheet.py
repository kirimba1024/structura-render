import hashlib
import json
from statistics import median
from time import perf_counter

from amulet_nbt import CompoundTag, IntTag, ListTag
from structura_core import Structure, parse_state

from structura_render import render_projections


def measure():
    source = Structure.from_root(CompoundTag({
        "DataVersion": IntTag(3955), "size": ListTag([IntTag(50), IntTag(20), IntTag(50)]),
        "palette": ListTag([parse_state("minecraft:stone")]),
        "blocks": ListTag(), "entities": ListTag(),
    }))
    source.present = {(x, y, z): 0 for x in range(50) for y in range(20) for z in range(50)}
    times = []
    for _ in range(4):
        start = perf_counter()
        image = render_projections(source, scale=1)
        times.append(perf_counter() - start)
    return {
        "blocks": len(source.present),
        "seconds_median": median(times[1:]),
        "pixels_sha256": hashlib.sha256(image.tobytes()).hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(measure(), indent=2))
