from server import PromptServer
from functools import reduce
import json


class Code:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "code": ("STRING", {"forceInput": True, "multiline": True, }),
            },
            "optional": {
                "lang": (["python", "json"], {"default": "python"},),
                "key": ("STRING", {"default": "function"},),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            }
        }

    CATEGORY = "Shibiko"
    COLOR = "#FFA800"
    DESCRIPTION = ("Designed to work with AnyNode by extracting the function code from the control output. "
                   "Will prettify the code. However, you can have this work with any JSON object or string."
                   " JSON object must be a string.")

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("code",)

    FUNCTION = "__call__"

    def __init__(self):
        pass

    @staticmethod
    def get_from_dict(data_dict, map_list):
        return reduce(lambda d, k: d.get(k) if d else None, map_list, data_dict)

    @staticmethod
    def send_code(code, id, lang="python"):
        PromptServer.instance.send_sync("code", { "code": code, "id": id, "lang": lang })

    @classmethod
    def IS_CHANGED(cls, code, lang, key, unique_id):
        return cls.__call__(code, lang, key, unique_id)

    def __call__(self, code="", lang='python', key=None, unique_id=None):
        if key is not None:
            key_list = key.split(".")
            code_dict = json.loads(code)
            code = self.get_from_dict(code_dict, key_list)

        self.send_code(code, unique_id, lang)
        return (code,)


NODE_CLASS_MAPPINGS = {"Code": Code}
NODE_DISPLAY_NAME_MAPPINGS = {"Code": "Shibiko AI - Code"}
