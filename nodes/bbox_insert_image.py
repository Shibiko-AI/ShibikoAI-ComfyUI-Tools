import numpy as np
import torch
import torch.nn.functional as F


class BboxInsertImage:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "bbox_image": ("IMAGE",),
                "bbox": ("BBOX",),
                "blend_factor": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.1}),
            }
        }

    CATEGORY = "Shibiko AI"
    DESCRIPTION = "Insert Image into Bounding Box Area with Smooth Blending."

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)

    FUNCTION = "__call__"

    def __call__(self, image, bbox_image, bbox, blend_factor=0.5):
        device = image.device
        bbox_image = bbox_image.to(device)

        if isinstance(bbox, (np.ndarray, torch.Tensor)):
            bbox = bbox.tolist()

        if len(bbox) == 1 and isinstance(bbox[0], (list, tuple)):
            bbox = bbox[0]

        if len(bbox) != 4:
            raise ValueError(f"Invalid bbox format. Expected 4 values, but got {len(bbox)}")

        x, y, w, h = map(int, bbox)

        # Ensure bbox_image has 4 dimensions (N, H, W, C)
        if bbox_image.dim() == 3:
            bbox_image = bbox_image.unsqueeze(0)

        # If bbox_image doesn't have a channel dimension, add it
        if bbox_image.shape[-1] != image.shape[-1]:
            bbox_image = bbox_image.unsqueeze(-1).repeat(1, 1, 1, image.shape[-1])

        # Get the dimensions of the original region
        original_region = image[:, y:y + h, x:x + w, :]
        original_h, original_w = original_region.shape[1:3]

        # Resize bbox_image to match the original region size
        bbox_image = F.interpolate(bbox_image.permute(0, 3, 1, 2),
                                   size=(original_h, original_w),
                                   mode='bilinear',
                                   align_corners=False)
        bbox_image = bbox_image.permute(0, 2, 3, 1)

        # Ensure bbox_image has the same batch size as image
        if bbox_image.shape[0] != image.shape[0]:
            bbox_image = bbox_image.repeat(image.shape[0], 1, 1, 1)

        # Create a Gaussian blending mask
        blend_mask = self.create_gaussian_mask(original_h, original_w, device)

        # Apply blending
        blended_image = blend_factor * bbox_image + (1 - blend_factor) * original_region
        blended_image = blend_mask * bbox_image + (1 - blend_mask) * original_region

        # Insert blended image into original image
        image[:, y:y + h, x:x + w, :] = blended_image

        return (image,)

    def create_gaussian_mask(self, height, width, device, sigma=10):
        """
        Creates a Gaussian blend mask that smoothly fades from the center outwards.
        """
        y, x = torch.meshgrid(torch.linspace(-1, 1, height, device=device),
                              torch.linspace(-1, 1, width, device=device), indexing='ij')

        distance = torch.sqrt(x ** 2 + y ** 2)
        mask = torch.exp(-distance ** 2 / (2 * sigma ** 2))
        mask = (mask - mask.min()) / (mask.max() - mask.min())  # Normalize to 0-1

        return mask.unsqueeze(0).unsqueeze(-1)  # Add batch and channel dims


NODE_CLASS_MAPPINGS = {"BboxInsertImage": BboxInsertImage}
NODE_DISPLAY_NAME_MAPPINGS = {"BboxInsertImage": "Shibiko AI - BBOX Insert Image"}
