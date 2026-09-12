import numpy as np


def srgb_to_linear(rgb):
    rgb = np.asarray(rgb, np.float64)
    return np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055)**2.4)


def linear_to_srgb(rgb):
    rgb = np.clip(rgb, 0, 1)
    return np.where(rgb <= 0.0031308, rgb * 12.92, 1.055 * rgb**(1 / 2.4) - 0.055)
