import torch
import numpy as np
from PIL import Image
from typing import Optional


class ShibikoAI_Waifu2x:
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "noise_level": ("INT", {"default": 3, "min": 0, "max": 3, "step": 1},),
                "scale": ([1, 2, 4],),
                "model_type": (["art", "photo"],),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID"
            },
        }

    CATEGORY = "Shibiko"

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("IMAGE",)

    FUNCTION = "__call__"

    def __init__(self, **kwargs):
        self.amp = kwargs.get('amp', False)
        self.batch_size = kwargs.get('batch_size', 1)
        self.keep_alpha = kwargs.get('keep_alpha', True)
        self.method = 'noise'
        self.model = None
        self.model_type = kwargs.get('model_type', 'art')
        self.noise_level = kwargs.get('noise_level', 3)
        self.output_type = kwargs.get('output_type', 'pil')
        self.scale = kwargs.get('scale', 1)
        self.tile_size = kwargs.get('tile_size', 256)

        self.load()

    def load(self, model_type: Optional[str] = 'art'):
        self.model = torch.hub.load(
            'nagadomi/nunif:dev',
            'waifu2x',
            model_type=model_type,
            batch_size=self.batch_size,
            keep_alpha=self.keep_alpha,
            amp=self.amp,
            trust_repo=True,
        ).to('cuda')

        self.method = self.waifu2x_method(self.scale, self.noise_level)
        self.model.set_mode(method=self.method, noise_level=self.noise_level)

    def set(
            self,
            amp: Optional[bool] = None,
            batch_size: Optional[int] = None,
            enabled: Optional[bool] = None,
            keep_alpha: Optional[bool] = None,
            model_type: Optional[str] = None,
            noise_level: Optional[int] = None,
            output_type: Optional[str] = None,
            scale: Optional[int] = None,
            tile_size: Optional[int] = None,
    ):
        settings = locals()
        settings.pop('self')
        for key, value in settings.items():
            if value:
                setattr(self, key, value)

    @staticmethod
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

    @staticmethod
    def waifu2x_method(scale, noise_level):
        if noise_level < 0 and scale <= 1:
            return None
        if noise_level >= 0 and scale <= 1:
            return 'noise'
        if noise_level < 0 and scale == 2:
            return 'scale'
        if noise_level >= 0 and scale == 2:
            return 'noise_scale'
        if noise_level < 0 and scale == 4:
            return 'scale4x'
        if noise_level >= 0 and scale == 4:
            return 'noise_scale4x'

    def __call__(
            self,
            image,
            scale: Optional[int] = 1,
            noise_level: Optional[int] = 3,
            model_type: Optional[str] = 'art',
            unique_id=None
    ):
        print(f'Waifu2x Upscaling image with unique_id: {unique_id} noise_level:{noise_level} scale:{scale}x model_type:{model_type}...')
        print(f'Type of image: {type(image)}')

        if self.model_type != model_type:
            self.load(model_type)

        image = self.convert(image)
        scale = scale if scale is not None else self.scale
        noise_level = noise_level if noise_level is not None else self.noise_level

        if self.scale != scale or self.noise_level != noise_level:
            self.method = self.waifu2x_method(scale, noise_level)
            self.model.set_mode(self.method, noise_level)
        image = self.model.infer(image, method=self.method, noise_level=noise_level, output_type='pil')
        image = self.convert(image)
        return (image,)

    # @classmethod
    # def IS_CHANGED(self, video, **kwargs):
    #     return hash_path(video)
    #
    # @classmethod
    # def VALIDATE_INPUTS(self, video, **kwargs):
    #     return validate_path(video, allow_none=True)


NODE_CLASS_MAPPINGS = {"Shibiko AI Waifu2X": ShibikoAI_Waifu2x}
NODE_DISPLAY_NAME_MAPPINGS = {"Shibiko AI Waifu2x": "Shibiko AI Waifu2X"}
