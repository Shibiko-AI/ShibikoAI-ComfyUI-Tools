import os
import importlib

WEB_DIRECTORY = "./web"
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}


def load_module(module_name):
    try:
        module = importlib.import_module(f'.nodes.{module_name}', package=__package__)
        NODE_CLASS_MAPPINGS.update(getattr(module, 'NODE_CLASS_MAPPINGS', {}))
        NODE_DISPLAY_NAME_MAPPINGS.update(getattr(module, 'NODE_DISPLAY_NAME_MAPPINGS', {}))
        print(f'\033[93m[Shibiko AI] \033[31m{module_name.capitalize()} \033[92mloaded\033[0m')
    except ImportError as e:
        print(f'\033[93m[Shibiko AI] \033[31mFailed to load {module_name}: {str(e)}\033[0m')


current_dir = os.path.dirname(os.path.abspath(__file__))
nodes_dir = os.path.join(current_dir, 'nodes')

for filename in os.listdir(nodes_dir):
    if filename.endswith('.py') and not filename.startswith('__'):
        load_module(filename[:-3])

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']
print(f'\033[93m[Shibiko AI] \033[92mLoading Complete!\033[0m')
