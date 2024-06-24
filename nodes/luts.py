import os
from PIL import ImageFilter
from typing import List, Union
from ..utils.convert import convert


class Luts:
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "image": ("IMAGE",),
                "lut": ("STRING", 'colorful.cube'),
            },
            "optional": {},
            "hidden": {
                "unique_id": "UNIQUE_ID"
            },
        }

    CATEGORY = "Shibiko"

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("IMAGE",)

    FUNCTION = "__call__"

    def __init__(self, **kwargs):
        pass

    def apply_lut(self, image, lut):
        print("Applying LUT...")
        base_directory = self.get_models_dir()
        if not lut.endswith(".cube"):
            lut += ".cube"
        lut_file_name = lut
        lut_path = os.path.join(base_directory, 'luts', f"{lut_file_name}")
        lut = self.read_lut(lut_path)

        if isinstance(image, list):
            image = [img.filter(lut) for img in image]
        else:
            image = image.filter(lut)

        return image

    def is_3dlut_row(self, row: List) -> bool:
        """Check if one line in the file has exactly 3 values"""
        row_values = []
        for val in row:
            try:
                row_values.append(float(val))
            except:
                return False
        if len(row_values) == 3:
            return True
        return False

    def read_lut(self, path_lut: Union[str, os.PathLike], num_channels: int = 3):
        """Read LUT from raw file. Assumes each line in a file is part of the lut table"""
        with open(path_lut) as f:
            lut_raw = f.read().splitlines()

        size = round(len(lut_raw) ** (1 / 3))
        lut_table = [
            self.row2val(row.split(" ")) for row in lut_raw if self.is_3dlut_row(row.split(" "))
        ]

        return ImageFilter.Color3DLUT(size, lut_table, num_channels)

    @staticmethod
    def row2val(row):
        return tuple([float(val) for val in row])

    @staticmethod
    def get_models_dir():
        current_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))

        while True:
            # Check if "ComfyUI/models" exists in the current path
            target_path = os.path.join(current_path, "ComfyUI", "models")
            if os.path.isdir(target_path):
                return os.path.abspath(target_path)

            # Move up one directory level
            new_path = os.path.dirname(current_path)
            if new_path == current_path:
                break
            current_path = new_path

        return None

    def __call__(self, image, lut, unique_id):
        image = convert(image)
        image = self.apply_lut(image, lut)
        image = convert(image)

        return (image,)


NODE_CLASS_MAPPINGS = {"Luts": Luts}
NODE_DISPLAY_NAME_MAPPINGS = {"Luts": "Shibiko AI - Luts"}
