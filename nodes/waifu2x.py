import torch
from typing import Optional
from ..utils.convert import convert, tensor2pil, pil2tensor


class Waifu2x:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "noise_level": ("INT", {"default": 3, "min": 0, "max": 3, "step": 1},),
                "scale": ([1, 2, 4],),
                "model_type": (["art", "photo"],),
            },
        }

    CATEGORY = "Shibiko AI"

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)

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
        **kwargs
    ):
        print('WAIFU2X CALL:', scale, noise_level, model_type)
        if self.model_type != model_type:
            self.load(model_type)

        if isinstance(image, torch.Tensor):
            if image.dim() == 3:
                image = [image]
            elif image.dim() == 4:
                image = [img for img in image]

        tensors = []
        for img in image:
            img = img.cpu()
            img_pil = tensor2pil(img)

            scale = scale if scale is not None else self.scale
            noise_level = noise_level if noise_level is not None else self.noise_level

            if self.scale != scale or self.noise_level != noise_level:
                self.method = self.waifu2x_method(scale, noise_level)
                self.model.set_mode(self.method, noise_level)

            print('METHOD:', self.method)

            img_pil = self.model.infer(img_pil, method=self.method, noise_level=noise_level, output_type='pil')

            img_tensor = pil2tensor(img_pil)
            tensors.append(img_tensor)

        if len(tensors) > 1:
            output = torch.cat(tensors, dim=0)
        else:
            output = tensors[0]

        if output.dtype != torch.float32:
            output = output.float()
        if output.max() > 1.0:
            output = output / 255.0

        return (output,)


NODE_CLASS_MAPPINGS = {"Waifu2x": Waifu2x}
NODE_DISPLAY_NAME_MAPPINGS = {"Waifu2x": "Shibiko AI - Waifu2X"}
