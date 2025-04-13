import torch
import numpy as np
from PIL import Image


def convert(image):
    if isinstance(image, Image.Image):
        img_array = np.array(image)
        img_tensor = torch.from_numpy(img_array).float() / 255.
        if img_tensor.ndim == 3 and img_tensor.shape[-1] == 3:
            img_tensor = img_tensor.permute(2, 0, 1)
        image = img_tensor.unsqueeze(0).permute(0, 2, 3, 1)

    elif isinstance(image, torch.Tensor):
        img_array = image.squeeze(0).cpu().numpy() * 255.0
        image = Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))

    return image


# Tensor to PIL
def tensor2pil(image):
    return Image.fromarray(np.clip(255. * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))


# PIL to Tensor
def pil2tensor(image):
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)
