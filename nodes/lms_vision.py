import torch
import numpy as np
from PIL import Image
import base64
import io
import requests
import subprocess
import json
import os
import logging
import time
from comfy.utils import ProgressBar

logger = logging.getLogger("LMS_Controller")


class LMS_CLI_Handler:
    _model_cache = None
    _last_cache_time = 0
    CACHE_TTL = 10

    @staticmethod
    def get_lms_path():
        if os.name == 'nt':
            user_home = os.path.expanduser("~")
            candidates = [
                os.path.join(user_home, ".lmstudio", "bin", "lms.exe"),
                os.path.join(user_home, "AppData", "Local", "LM-Studio", "app", "bin", "lms.exe")
            ]
            for path in candidates:
                if os.path.exists(path):
                    return path
            return "lms"

    @staticmethod
    def run_cmd(args, timeout=30):
        lms_path = LMS_CLI_Handler.get_lms_path()
        cmd = [lms_path] + args
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='replace',
                startupinfo=startupinfo
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    @classmethod
    def get_models(cls):
        if cls._model_cache and (time.time() - cls._last_cache_time < cls.CACHE_TTL):
            return cls._model_cache

        success, stdout, stderr = cls.run_cmd(["ls"], timeout=5)
        if not success:
            logger.error(f"LMS LS Error: {stderr}")
            return ["Error: lms ls failed"]

        models = []
        lines = stdout.strip().splitlines()
        BLACKLIST = {
            "size", "ram", "type", "architecture", "model", "path",
            "llm", "llms", "embedding", "embeddings", "vision", "image",
            "name", "loading", "fetching", "downloaded", "bytes", "date",
            "publisher", "repository", "you", "have", "features", "primary", "gpu"
        }
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if all(c in "-=*" for c in line):
                continue
            parts = line.split()
            if not parts:
                continue
            raw_name = parts[0]
            raw_lower = raw_name.lower()
            if raw_lower.rstrip(":") in BLACKLIST:
                continue
            if raw_lower[0].isdigit() and ("gb" in raw_lower or "mb" in raw_lower):
                continue
            clean_name = raw_name
            if "/" in clean_name:
                clean_name = clean_name.split("/")[-1]
            if clean_name.lower().endswith(".gguf"):
                clean_name = clean_name[:-5]
            if len(clean_name) < 2:
                continue
            models.append(clean_name)
        unique_models = sorted(list(set(models)))
        if not unique_models:
            unique_models = ["No models found"]
        cls._model_cache = unique_models
        cls._last_cache_time = time.time()
        return unique_models

    @classmethod
    def load_model(cls, model_name, identifier, gpu_ratio=1.0, context_length=2048):
        logger.info(f"LMS: Loading '{model_name}' (GPU: {gpu_ratio}, Ctx: {context_length})...")
        gpu_arg = "max" if gpu_ratio >= 1.0 else str(gpu_ratio)
        if gpu_ratio <= 0:
            gpu_arg = "0"
        args = ["load", model_name, "--identifier", identifier, "--gpu", gpu_arg, "--context-length", str(context_length)]
        success, stdout, stderr = cls.run_cmd(args, timeout=180)
        if not success:
            logger.error(f"LMS Load Error: {stderr}")
        return success

    @classmethod
    def unload_all(cls):
        success, _, stderr = cls.run_cmd(["unload", "--all"], timeout=20)
        return success


class LMS_VisionController:
    _current_loaded_model = None
    _current_gpu_ratio = 1.0
    _current_context = 2048

    def __init__(self):
        self.cli = LMS_CLI_Handler()

    @classmethod
    def INPUT_TYPES(cls):
        model_list = LMS_CLI_Handler.get_models()
        return {
            "required": {
                "user_prompt": ("STRING", {"multiline": True, "default": "Describe the content of the images/video."}),
                "model_name": (model_list,),
                "max_total_images": ("INT", {"default": 8, "min": 1, "max": 64}),
                "gpu_offload": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.05}),
                "context_length": ("INT", {"default": 8192, "min": 512, "max": 32768}),
                "max_image_side": ("INT", {"default": 1024, "min": 256, "max": 4096}),
                "max_tokens": ("INT", {"default": 1024, "min": 1, "max": 32768}),
                "temperature": ("FLOAT", {"default": 0.6, "min": 0.0, "max": 2.0, "step": 0.05}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "unload_after": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "image": ("IMAGE",),
                "image_2": ("IMAGE",),
                "image_3": ("IMAGE",),
                "video_frames": ("IMAGE",),
                "system_prompt": ("STRING", {"multiline": True, "default": "You are a helpful AI assistant."}),
                "base_url": ("STRING", {"default": "http://localhost:1234/v1"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response_text",)
    FUNCTION = "generate_content"
    CATEGORY = "Shibiko AI"

    def process_image(self, tensor_img, max_side):
        try:
            img_np = (tensor_img.cpu().numpy() * 255).clip(0, 255).astype(np.uint8)
            pil_img = Image.fromarray(img_np)
            if pil_img.mode != 'RGB':
                pil_img = pil_img.convert('RGB')
            width, height = pil_img.size
            if max(width, height) > max_side:
                ratio = max_side / max(width, height)
                new_size = (int(width * ratio), int(height * ratio))
                pil_img = pil_img.resize(new_size, Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            pil_img.save(buffer, format="JPEG", quality=85)
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
        except Exception as e:
            logger.error(f"Image processing error: {e}")
            return None

    def generate_content(self, user_prompt, model_name, max_total_images, gpu_offload, context_length, max_image_side,
                        max_tokens, temperature, seed, unload_after,
                        image=None, image_2=None, image_3=None, video_frames=None,
                        system_prompt="", base_url="http://localhost:1234/v1", **kwargs):

        if "http" not in base_url:
            base_url = "http://localhost:1234/v1"
        IDENTIFIER = "comfy_vlm_worker"

        # Collect images
        all_tensors = []
        if image is not None:
            for i in range(image.shape[0]):
                all_tensors.append(image[i])
        if image_2 is not None:
            for i in range(image_2.shape[0]):
                all_tensors.append(image_2[i])
        if image_3 is not None:
            for i in range(image_3.shape[0]):
                all_tensors.append(image_3[i])
        if video_frames is not None:
            for i in range(video_frames.shape[0]):
                all_tensors.append(video_frames[i])

        # Validate input
        total_count = len(all_tensors)
        if total_count == 0:
            return ("Error: No images or video frames provided. Please connect at least one input.",)

        # Frame sampling
        final_tensors = []
        if total_count > max_total_images:
            indices = np.linspace(0, total_count - 1, max_total_images, dtype=int)
            final_tensors = [all_tensors[i] for i in indices]
        else:
            final_tensors = all_tensors

        # Initialize progress bar - total steps: image processing + model loading + API request
        total_steps = len(final_tensors) + 2  # images + load model + API request
        pbar = ProgressBar(total_steps)

        # Convert to Base64 with progress tracking
        image_content_list = []
        for idx, tensor in enumerate(final_tensors):
            pbar.update_absolute(idx, total_steps, f"Processing image {idx + 1}/{len(final_tensors)}")
            b64 = self.process_image(tensor, max_image_side)
            if b64:
                image_content_list.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                })

        if not image_content_list:
            return ("Error: No valid images processed.",)

        # Load model with progress tracking
        pbar.update_absolute(len(final_tensors), total_steps, "Loading model...")
        needs_reload = (
            LMS_VisionController._current_loaded_model != model_name or
            abs(LMS_VisionController._current_gpu_ratio - gpu_offload) > 0.01 or
            LMS_VisionController._current_context != context_length
        )

        if needs_reload:
            self.cli.unload_all()
            time.sleep(1.0)
            success = self.cli.load_model(model_name, IDENTIFIER, gpu_ratio=gpu_offload, context_length=context_length)
            if success:
                LMS_VisionController._current_loaded_model = model_name
                LMS_VisionController._current_gpu_ratio = gpu_offload
                LMS_VisionController._current_context = context_length
                time.sleep(2.0)
            else:
                return (f"Error: Failed to load model '{model_name}'.",)

        # Send API request with progress tracking
        pbar.update_absolute(len(final_tensors) + 1, total_steps, "Generating response...")
        user_content = [{"type": "text", "text": user_prompt}] + image_content_list
        payload = {
            "model": IDENTIFIER,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "seed": seed,
            "stream": False
        }

        content = ""
        try:
            api_endpoint = f"{base_url.rstrip('/')}/chat/completions"
            response = requests.post(api_endpoint, headers={"Content-Type": "application/json"}, json=payload, timeout=300)
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content']
                else:
                    content = "Error: Empty response."
            else:
                content = f"API Error {response.status_code}: {response.text}"
                logger.error(content)
        except Exception as e:
            content = f"Connection Error: {str(e)}"
            logger.error(content)

        # Complete progress
        pbar.update_absolute(total_steps, total_steps, "Complete")

        if unload_after:
            self.cli.unload_all()
            LMS_VisionController._current_loaded_model = None

        return (content,)


NODE_CLASS_MAPPINGS = {"LMS_VisionController": LMS_VisionController}
NODE_DISPLAY_NAME_MAPPINGS = {"LMS_VisionController": "Shibiko AI - LM Studio Vision"}
