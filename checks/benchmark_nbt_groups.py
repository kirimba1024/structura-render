import json
import tracemalloc
from time import perf_counter
from types import SimpleNamespace

import numpy as np

from structura_render.mesh_models import instance_groups, instance_positions


def measure(grouping):
    source = SimpleNamespace(block_nbt={
        (i, 0, 0): {"sherds": [f"minecraft:variant_{i}_pottery_sherd"] * 4}
        for i in range(100)
    })
    state = np.full((100, 100, 100), -1, dtype=np.int32)
    state[:, 0, 0] = 0
    tracemalloc.start()
    start = perf_counter()
    groups = grouping(source, state, 0, "minecraft:decorated_pot")
    elapsed = perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "groups": len(groups),
        "retained_array_bytes": sum(array.nbytes for array in groups.values()),
        "peak_bytes": peak,
        "seconds": elapsed,
    }


if __name__ == "__main__":
    print(json.dumps({"dense_compatibility": measure(instance_groups),
                      "compact": measure(instance_positions)}, indent=2))
