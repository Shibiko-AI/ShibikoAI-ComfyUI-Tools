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

    CATEGORY = "Shibiko AI"

    RETURN_TYPES = ("IMAGE", "MASK", "BBOX")
    RETURN_NAMES = ("image", "mask", "bbox")

    FUNCTION = "__call__"

    def __init__(self, cascade='frontalface_default', padding=25):
        self.cascades_directory = None
        self.cascade = cascade
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
        if len(image.shape) > 2:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        return self.haar_cascade_face.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(32, 32))

    @staticmethod
    def draw(image, bbox, padding):
        image = image.copy()
        for (x, y, w, h) in bbox:
            cv2.rectangle(image, (x - padding, y - padding), (x + w + padding, y + h + padding), (255, 0, 0), 2)
        return image

    def mask(self, image, bbox, blur=25, blur_type='gaussian', dilation=4, padding=4):
        mask = np.zeros_like(image)
        for (x, y, w, h) in bbox:
            mask[y - padding:y + h + padding, x - padding:x + w + padding] = 255

        if blur > 0:
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
        return torch.from_numpy(image_rgb)

    def __call__(self, image, blur=25, blur_type='gaussian', cascade=None, dilation=4, padding=4, **kwargs):
        if cascade is not None and cascade != self.cascade:
            self.load(cascade)

        if image.ndim == 3:
            image = image.unsqueeze(0)

        images = []
        masks = []
        all_bboxes = []

        for i in range(image.shape[0]):
            img = image[i]
            cv2_img = self.NHWC_to_CV2(img)
            bbox = self.detect(cv2_img)
            drawn = self.draw(cv2_img, bbox, padding)
            mask = self.mask(cv2_img, bbox, blur, blur_type, dilation, padding)
            final = self.CV2_to_NHWC(drawn)
            images.append(final)
            masks.append(mask)
            all_bboxes.append(bbox.tolist() if len(bbox) > 0 else [])

        images_tensor = torch.cat(images, dim=0)
        masks_tensor = torch.cat(masks, dim=0)

        return images_tensor, masks_tensor, all_bboxes


NODE_CLASS_MAPPINGS = {"Cascade": Cascade}
NODE_DISPLAY_NAME_MAPPINGS = {"Cascade": "Shibiko AI - Cascade Detection"}
