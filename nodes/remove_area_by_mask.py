import cv2
import numpy as np
import torch


class RemoveAreaByMask:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "mask": ("MASK",),
            },
            "optional": {
                "invert_mask": ("BOOLEAN", {"default": False}),
            },
        }

    CATEGORY = "Shibiko AI"

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)

    FUNCTION = "__call__"

    @staticmethod
    def NHWC_to_CV2(image):
        image_numpy = image.cpu().numpy()
        return (image_numpy[0] * 255).astype(np.uint8)  # Convert to uint8, keep NHWC

    @staticmethod
    def CV2_to_NHWC(image):
        image_rgb = image.astype(np.float32) / 255.0
        return torch.from_numpy(image_rgb).unsqueeze(0)  # (1, H, W, C)

    def __call__(self, image, mask, invert_mask=False):
        image_cv2 = self.NHWC_to_CV2(image)
        mask_cv2 = self.NHWC_to_CV2(mask)

        if mask_cv2.ndim == 3 and mask_cv2.shape[2] == 3:
            mask_cv2 = cv2.cvtColor(mask_cv2, cv2.COLOR_BGR2GRAY)

        if mask_cv2.shape[:2] != image_cv2.shape[:2]:
            mask_cv2 = cv2.resize(mask_cv2, (image_cv2.shape[1], image_cv2.shape[0]), interpolation=cv2.INTER_NEAREST)

        mask_float = mask_cv2.astype(np.float32) / 255.0

        if mask_float.ndim == 2:
            mask_float = np.expand_dims(mask_float, axis=-1)

        if invert_mask:
            mask_float = 1.0 - mask_float

        masked_image = (image_cv2 * (1 - mask_float)).astype(np.uint8)

        return (self.CV2_to_NHWC(masked_image),)  # Return (1, H, W, C)


NODE_CLASS_MAPPINGS = {"RemoveAreaByMask": RemoveAreaByMask}
NODE_DISPLAY_NAME_MAPPINGS = {"RemoveAreaByMask": "Shibiko AI - Remove Area By Mask"}
