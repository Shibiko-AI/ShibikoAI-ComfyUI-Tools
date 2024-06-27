import os
import shutil
from typing import LiteralString


def get_models_dir():
    current_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))

    while True:
        # Check if "ComfyUI/models" exists in the current path
        target_path = os.path.join(current_path, "ComfyUI", "models")
        if os.path.isdir(target_path):
            return os.path.abspath(target_path)

        # Move up one directory level
        new_path = os.path.dirname(current_path)
        if new_path == current_path:
            break
        current_path = new_path

    return None


def initialize_directory(directory_name):
    base_directory = get_models_dir()
    target_directory = os.path.join(base_directory, directory_name)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    source_directory = os.path.join(script_dir, '..', 'assets', directory_name)

    if not (os.path.exists(target_directory) and os.path.isdir(target_directory)):
        os.makedirs(target_directory)
        # Copy files from source_directory to target_directory
        for filename in os.listdir(source_directory):
            src_file = os.path.join(source_directory, filename)
            dst_file = os.path.join(target_directory, filename)
            if os.path.isfile(src_file):
                shutil.copy(src_file, dst_file)

    return target_directory
