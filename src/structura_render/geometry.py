"""NumPy geometry shared by file exporters and the optional image backend."""

from dataclasses import dataclass

import numpy as np

DEFAULT_MAX_VOXELS = 16_000_000


@dataclass
class TexturedMesh:
    points: np.ndarray
    quads: np.ndarray
    uv: np.ndarray
    alpha_modes: np.ndarray
    image: np.ndarray

    def to_pyvista(self):
        import pyvista as pv

        faces = np.column_stack((np.full(len(self.quads), 4), self.quads)).ravel()
        mesh = pv.PolyData(self.points, faces)
        mesh.active_texture_coordinates = self.uv
        mesh.cell_data["alpha_mode"] = self.alpha_modes
        texture = pv.Texture(self.image)
        texture.SetInterpolate(False)
        texture.mipmap = False
        return mesh, texture
