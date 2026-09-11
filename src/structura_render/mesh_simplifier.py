import ctypes
from functools import lru_cache

import numpy as np


@lru_cache(maxsize=1)
def attribute_simplifier():
    from meshoptimizer._loader import lib

    uints = np.ctypeslib.ndpointer(dtype=np.uint32, flags="C_CONTIGUOUS")
    floats = np.ctypeslib.ndpointer(dtype=np.float32, flags="C_CONTIGUOUS")
    bytes_array = np.ctypeslib.ndpointer(dtype=np.uint8, flags="C_CONTIGUOUS")
    size = ctypes.c_size_t
    signature = ctypes.CFUNCTYPE(size, uints, uints, size, floats, size, size,
                                floats, size, floats, size, bytes_array, size,
                                ctypes.c_float, ctypes.c_uint, floats)
    return signature(("meshopt_simplifyWithAttributes", lib))


def simplify_attributes(indices, points, colors, locked, target_count, error):
    import meshoptimizer

    destination = np.empty_like(indices)
    attributes = np.ascontiguousarray(colors, np.float32) / 255
    weights = np.full(4, 0.5, np.float32)
    result_error = np.zeros(1, np.float32)
    count = attribute_simplifier()(
        destination, indices, len(indices), points, len(points), points.strides[0],
        attributes, attributes.strides[0], weights, len(weights), locked, target_count,
        error, meshoptimizer.SIMPLIFY_ERROR_ABSOLUTE, result_error)
    return destination[:count], float(result_error[0])
