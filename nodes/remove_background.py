import os
import torch
import folder_paths
from rembg import remove, new_session
from ..utils.convert import pil2tensor, tensor2pil
from comfy.utils import ProgressBar


class RemoveBackground:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "transparency": ("BOOLEAN", {"default": True},),
                "model": (["u2net", "u2netp", "u2net_human_seg", "silueta", "isnet-general-use", "isnet-anime"], {"default": "isnet-anime"}),
                "post_processing": ("BOOLEAN", {"default": False}),
                "only_mask": ("BOOLEAN", {"default": False},),
                "alpha_matting": ("BOOLEAN", {"default": False},),
                "alpha_matting_foreground_threshold": ("INT", {"default": 240, "min": 0, "max": 255}),
                "alpha_matting_background_threshold": ("INT", {"default": 10, "min": 0, "max": 255}),
                "alpha_matting_erode_size": ("INT", {"default": 10, "min": 0, "max": 255}),
                "background_color": (["none", "black", "white", "magenta", "chroma green", "chroma blue"],),
                "putalpha": ("BOOLEAN", {"default": False},),
            },
        }

    CATEGORY = "Shibiko AI"

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)

    FUNCTION = "__call__"

    # A helper function to convert from strings to logical boolean
    # Conforms to https://docs.python.org/3/library/stdtypes.html#truth-value-testing
    # With the addition of evaluating string representations of Falsy types
    @staticmethod
    def __convertToBool(x):

        # Evaluate string representation of False types
        if type(x) is str:
            x = x.strip()
            if (x.lower() == 'false'
                    or x.lower() == 'none'
                    or x == '0'
                    or x == '0.0'
                    or x == '0j'
                    or x == "''"
                    or x == '""'
                    or x == "()"
                    or x == "[]"
                    or x == "{}"
                    or x.lower() == "decimal(0)"
                    or x.lower() == "fraction(0,1)"
                    or x.lower() == "set()"
                    or x.lower() == "range(0)"):
                return False
            else:
                return True

        return bool(x)

    def __call__(
        self,
        images,
        transparency=True,
        model="isnet-anime",
        alpha_matting=False,
        alpha_matting_foreground_threshold=240,
        alpha_matting_background_threshold=10,
        alpha_matting_erode_size=10,
        post_processing=False,
        only_mask=False,
        background_color="none",
        putalpha=False,
        **kwargs
    ):
        # ComfyUI will allow strings in place of booleans, validate the input.
        transparency = transparency if type(transparency) is bool else self.__convertToBool(transparency)
        alpha_matting = alpha_matting if type(alpha_matting) is bool else self.__convertToBool(alpha_matting)
        post_processing = post_processing if type(post_processing) is bool else self.__convertToBool(post_processing)
        only_mask = only_mask if type(only_mask) is bool else self.__convertToBool(only_mask)

        os.environ['U2NET_HOME'] = os.path.join(folder_paths.models_dir, 'rembg')
        os.makedirs(os.environ['U2NET_HOME'], exist_ok=True)

        # Set background color
        if background_color == "black":
            bgrgba = [0, 0, 0, 255]
        elif background_color == "white":
            bgrgba = [255, 255, 255, 255]
        elif background_color == "magenta":
            bgrgba = [255, 0, 255, 255]
        elif background_color == "chroma green":
            bgrgba = [0, 177, 64, 255]
        elif background_color == "chroma blue":
            bgrgba = [0, 71, 187, 255]
        else:
            bgrgba = None

        if transparency and bgrgba is not None:
            bgrgba[3] = 0

        batch_tensor = []
        pbar = ProgressBar(len(images))
        for idx, image in enumerate(images):
            pbar.update_absolute(idx, len(images), f"Removing background from image {idx + 1}/{len(images)}")
            image = tensor2pil(image)
            batch_tensor.append(pil2tensor(
                remove(
                    image,
                    session=new_session(model),
                    post_process_mask=post_processing,
                    alpha_matting=alpha_matting,
                    alpha_matting_foreground_threshold=alpha_matting_foreground_threshold,
                    alpha_matting_background_threshold=alpha_matting_background_threshold,
                    alpha_matting_erode_size=alpha_matting_erode_size,
                    only_mask=only_mask,
                    bgcolor=bgrgba,
                    putalpha=putalpha,
                )
                .convert(('RGBA' if transparency else 'RGB'))))
        pbar.update_absolute(len(images), len(images), "Complete")
        batch_tensor = torch.cat(batch_tensor, dim=0)

        return (batch_tensor,)


NODE_CLASS_MAPPINGS = {"RemoveBackground": RemoveBackground}
NODE_DISPLAY_NAME_MAPPINGS = {"RemoveBackground": "Shibiko AI - Remove Background"}
