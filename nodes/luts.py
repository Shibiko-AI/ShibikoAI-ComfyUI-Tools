import os

import folder_paths
import numpy as np
import torch
from pathlib import Path
from PIL import ImageFilter
from colour.io.luts.iridas_cube import read_LUT_IridasCube
from typing import List, Union
from ..utils.convert import convert, tensor2pil, pil2tensor
from ..utils.directory import initialize_directory


class Luts:
    luts_directory = initialize_directory('luts')

    @classmethod
    def INPUT_TYPES(cls):
        luts = [lut.split(".")[0] for lut in os.listdir(cls.luts_directory) if lut.endswith(".cube")]

        return {
            "required": {
                "image": ("IMAGE",),
                "lut": (luts, {"default": 'Cinematic'}),
            },
        }

    CATEGORY = "Shibiko AI"

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)

    FUNCTION = "__call__"

    def apply_lut(self, image, lut):
        if not lut.endswith(".cube"):
            lut += ".cube"
        lut_file_name = lut
        lut_directory = initialize_directory('luts')
        lut_path = os.path.join(lut_directory, lut_file_name)
        lut_filter = self.read_lut(lut_path)

        # Convert tensor to PIL, apply LUT, then convert back to tensor
        if isinstance(image, torch.Tensor):
            image = tensor2pil(image)

        # Apply the LUT filter
        image = image.filter(lut_filter)

        return image

    def read_lut(self, path_lut: Union[str, os.PathLike], num_channels: int = 3):
        """Read LUT from raw file. Assumes each line in a file is part of the lut table"""
        with open(path_lut) as f:
            lut_raw = f.read().splitlines()

        size = round(len(lut_raw) ** (1 / 3))
        lut_table = [
            self.row2val(row.split(" ")) for row in lut_raw if self.is_3D_lut_row(row.split(" "))
        ]

        return ImageFilter.Color3DLUT(size, lut_table, num_channels)

    @staticmethod
    def is_3D_lut_row(row: List) -> bool:
        """Check if one line in the file has exactly 3 values"""
        row_values = []
        for val in row:
            try:
                row_values.append(float(val))
            except ValueError:
                return False
        return len(row_values) == 3

    @staticmethod
    def row2val(row):
        return tuple([float(val) for val in row])

    def __call__(self, image, lut, **kwargs):
        # Handle single image or batch
        if image.dim() == 3:  # Single image (H, W, C)
            images = [image]
        else:  # Batch of images (B, H, W, C)
            images = [img for img in image]

        processed_images = []
        for img in images:
            # Convert to PIL
            img_pil = tensor2pil(img)

            # Apply LUT
            img_processed = self.apply_lut(img_pil, lut)

            # Convert back to tensor
            img_tensor = pil2tensor(img_processed)
            processed_images.append(img_tensor)

        # Stack all tensors if we have multiple images
        if len(processed_images) > 1:
            output = torch.cat(processed_images, dim=0)
        else:
            output = processed_images[0]

        # Ensure proper output format (B, H, W, C) with float32 dtype
        if output.dtype != torch.float32:
            output = output.float()
        if output.max() > 1.0:
            output = output / 255.0

        return (output,)


# From https://github.com/yoonsikp/pycubelut/blob/master/pycubelut.py (MIT license)
class LutsAdvanced:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "lut_file": (os.listdir(os.path.join(folder_paths.models_dir, "luts")), {"default": "Cinematic.cube"}),
                "gamma_correction": ("BOOLEAN", {"default": True}),
                "clip_values": ("BOOLEAN", {"default": True}),
                "strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.1}),
            }}

    CATEGORY = "Shibiko AI"

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)

    FUNCTION = "__call__"

    # TODO: check if we can do without numpy
    def __call__(self, image, lut_file="cinematic", gamma_correction=True, clip_values=True, strength=1.0):
        lut_file_path = folder_paths.get_full_path("luts", lut_file + '.cube')
        if not lut_file_path or not Path(lut_file_path).exists():
            print(f"Could not find LUT file: {lut_file_path}")
            return (image,)

        device = image.device
        lut = read_LUT_IridasCube(lut_file_path)
        lut.name = lut_file

        if clip_values:
            if lut.domain[0].max() == lut.domain[0].min() and lut.domain[1].max() == lut.domain[1].min():
                lut.table = np.clip(lut.table, lut.domain[0, 0], lut.domain[1, 0])
            else:
                for dim in range(3):
                    domain0 = lut.domain[0, dim]
                    domain1 = lut.domain[1, dim]

                    if len(lut.table.shape) == 2:
                        lut.table[:, dim] = np.clip(lut.table[:, dim], domain0, domain1)
                    else:  # 3D
                        lut.table[:, :, :, dim] = np.clip(lut.table[:, :, :, dim], domain0, domain1)

        out = []
        for img in image:  # TODO: is this more resource efficient? should we use a batch instead?
            lut_img = img.cpu().numpy().copy()

            is_non_default_domain = not np.array_equal(lut.domain, np.array([[0., 0., 0.], [1., 1., 1.]]))
            dom_scale = None
            if is_non_default_domain:
                dom_scale = lut.domain[1] - lut.domain[0]
                lut_img = lut_img * dom_scale + lut.domain[0]

            if gamma_correction:
                lut_img = lut_img ** (1 / 2.2)

            lut_img = lut.apply(lut_img)
            if gamma_correction:
                lut_img = lut_img ** 2.2

            if is_non_default_domain:
                lut_img = (lut_img - lut.domain[0]) / dom_scale

            lut_img = torch.from_numpy(lut_img).to(device)
            if strength < 1.0:
                lut_img = strength * lut_img + (1 - strength) * img
            out.append(lut_img)

        out = torch.stack(out)

        return (out,)


NODE_CLASS_MAPPINGS = {
    "Luts": Luts,
    "LutsAdvanced": LutsAdvanced
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "Luts": "Shibiko AI - Luts",
    "LutsAdvanced": "Shibiko AI - Luts (Advanced)"
}
