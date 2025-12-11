# Original implementation from toyxyz/ComfyUI_toyxyz_test_nodes
# Source: https://github.com/toyxyz/ComfyUI_toyxyz_test_nodes/blob/main/nodes/toyxyz_test_nodes.py

import numpy as np
import torch
import cv2

MAX_RESOLUTION = 8192


class RemoveNoise:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "guided_first": ("BOOLEAN", {"default": True}),
                "bilateral_loop": ("INT", {"default": 1, "min": 0, "max": MAX_RESOLUTION, "step": 1}),
                "d": ("INT", {"default": 15, "min": 0, "max": MAX_RESOLUTION, "step": 1}),
                "sigma_color": ("INT", {"default": 45, "min": 0, "max": MAX_RESOLUTION, "step": 1}),
                "sigma_space": ("INT", {"default": 45, "min": 0, "max": MAX_RESOLUTION, "step": 1}),
                "guided_loop": ("INT", {"default": 4, "min": 0, "max": MAX_RESOLUTION, "step": 1}),
                "radius": ("INT", {"default": 4, "min": 0, "max": MAX_RESOLUTION, "step": 1}),
                "eps": ("INT", {"default": 16, "min": 0, "max": MAX_RESOLUTION, "step": 1}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "execute"
    CATEGORY = "Shibiko AI"

    def execute(self, image: torch.Tensor, bilateral_loop: int, d: int, sigma_color: int,
                sigma_space: int, guided_loop: int, radius: int, eps: int, guided_first: bool):

        diameter = d
        if diameter % 2 == 0:
            diameter += 1

        def sub(image: torch.Tensor):
            guide = np.clip(255.0 * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8)
            dst = guide.copy()

            if guided_first:
                if guided_loop > 0:
                    for _ in range(guided_loop):
                        dst = cv2.ximgproc.guidedFilter(guide, dst, radius, eps)

                if bilateral_loop > 0:
                    for _ in range(bilateral_loop):
                        dst = cv2.bilateralFilter(dst, diameter, sigma_color, sigma_space)
            else:
                if bilateral_loop > 0:
                    for _ in range(bilateral_loop):
                        dst = cv2.bilateralFilter(dst, diameter, sigma_color, sigma_space)

                if guided_loop > 0:
                    for _ in range(guided_loop):
                        dst = cv2.ximgproc.guidedFilter(guide, dst, radius, eps)

            return torch.from_numpy(dst.astype(np.float32) / 255.0).unsqueeze(0)

        if len(image) > 1:
            tensors = []
            for child in image:
                tensor = sub(child)
                tensors.append(tensor)
            return (torch.cat(tensors, dim=0),)
        else:
            tensor = sub(image)
            return (tensor,)


NODE_CLASS_MAPPINGS = {"RemoveNoise": RemoveNoise}
NODE_DISPLAY_NAME_MAPPINGS = {"RemoveNoise": "Shibiko AI - Remove Noise"}
