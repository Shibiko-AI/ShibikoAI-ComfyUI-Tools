import cv2
import numpy as np
import re
import os
import torch
from typing import Optional
from ..utils.directory import initialize_directory


class Cascade:
    cascades_directory = initialize_directory('cascades')

    @classmethod
    def INPUT_TYPES(cls):
        cascades = [cascade.split(".")[0] for cascade in os.listdir(cls.cascades_directory) if cascade.endswith(".xml")]
        embedded = [re.sub(r'haarcascade_|.xml', '', cascade) for cascade in os.listdir(cv2.data.haarcascades) if cascade.endswith(".xml")]

        cascades.extend(embedded)
        cascades.sort()

        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "cascade": (cascades, {"default": 'frontalface_default'}),
                "blur": ("INT", {"default": 32, "min": 0, "max": 100, "step": 1},),
                "blur_type": (["gaussian", "median", "box"], {"default": "box"}),
                "dilation": ("INT", {"default": 4, "min": 0, "step": 1},),
                "padding": ("INT", {"default": 4, "min": 0, "step": 1},),
            },
        }

    CATEGORY = "Shibiko"

    RETURN_TYPES = ("IMAGE", "MASK", "BBOX")
    RETURN_NAMES = ("image", "mask", "bbox")

    FUNCTION = "__call__"

    def __init__(self, cascade='frontalface_default', padding=25):
        self.cascades_directory = None
        self.cascade = cascade
        self.bbox = None
        self.image = None
        self.haar_cascade_face = None
        self.padding = padding

        self.load(cascade)

    def load(self, cascade='frontalface_default'):
        self.cascade = cascade
        self.cascades_directory = initialize_directory('cascades')

        cascade_path = os.path.join(self.cascades_directory, f'{cascade}.xml')
        if os.path.exists(self.cascades_directory) and os.path.exists(cascade_path):
            self.haar_cascade_face = cv2.CascadeClassifier(cascade_path)
        elif cv2.data.haarcascades not in cascade and 'haarcascade_' not in cascade:
            cascade_path = os.path.join(cv2.data.haarcascades, f'haarcascade_{cascade}.xml')
            self.haar_cascade_face = cv2.CascadeClassifier(cascade_path)
        else:
            raise ValueError('Invalid cascade path or name')

    def detect(self, image):
        self.image = image

        # Check Frame Color
        if len(self.image.shape) > 2:
            gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        else:
            gray = self.image

        # Detect faces in the image
        self.bbox = self.haar_cascade_face.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(24, 24))
        return self.bbox

    def draw(self, image=None, padding=None):
        if image is not None:
            self.image = image.copy()

        if padding is None:
            padding = self.padding

        # Draw rectangles around the faces
        for (x, y, w, h) in self.bbox:
            cv2.rectangle(self.image, (x - padding, y - padding), (x + w + padding, y + h + padding), (255, 0, 0), 2)

        return self.image

    def mask(self, blur=25, blur_type='gaussian', dilation=4, padding: Optional[int] = None):
        if self.bbox is None or self.image is None:
            raise ValueError('Cascades or image not detected')

        if padding is not None:
            self.padding = padding

        mask = self.image.copy()
        mask.fill(0)

        # Whiteout the detected faces on the mask
        for (x, y, w, h) in self.bbox:
            mask[y - self.padding:y + h + self.padding, x - self.padding:x + w + self.padding] = 255

        if blur is not None:
            if blur_type == 'gaussian':
                blur = blur if blur % 2 == 1 else blur + 1
                dilation = dilation if dilation % 2 == 1 else dilation + 1
                mask = cv2.GaussianBlur(mask, (blur, blur), 0)
            elif blur_type == 'median':
                blur = blur if blur % 2 == 1 else blur + 1
                dilation = dilation if dilation % 2 == 1 else dilation + 1
                mask = cv2.medianBlur(mask, blur)
            elif blur_type == 'box':
                mask = cv2.blur(mask, (blur, blur))
            else:
                pass

        kernel = np.ones((dilation, dilation), np.uint8)
        mask_dilated = cv2.dilate(mask, kernel, iterations=1)

        return self.CV2_to_NHWC(mask_dilated, cv2.COLOR_BGR2GRAY)

    @staticmethod
    def NHWC_to_CV2(image):
        image_numpy = image.squeeze().cpu().numpy()
        image_bgr = image_numpy[:, :, [2, 1, 0]]
        image_bgr = (image_bgr * 255).astype(np.uint8)

        return image_bgr

    @staticmethod
    def CV2_to_NHWC(image, code=cv2.COLOR_BGR2RGB):
        image_rgb = cv2.cvtColor(image, code)
        image_rgb = image_rgb.astype(np.float32) / 255.0
        image_rgb = image_rgb[np.newaxis, :]
        image_tensor = torch.from_numpy(image_rgb)

        return image_tensor

    def __call__(
        self,
        image,
        blur=25,
        blur_type='gaussian',
        cascade='frontalface_default',
        dilation=4,
        padding=50,
    ):
        if cascade != self.cascade:
            self.load(cascade)

        image = self.NHWC_to_CV2(image)
        self.detect(image)
        self.draw(image, padding)
        mask = self.mask(blur, blur_type, dilation, padding)

        return self.CV2_to_NHWC(self.image), mask, self.bbox


NODE_CLASS_MAPPINGS = {"Cascade": Cascade}
NODE_DISPLAY_NAME_MAPPINGS = {"Cascade": "Shibiko AI - Cascade Detection"}
