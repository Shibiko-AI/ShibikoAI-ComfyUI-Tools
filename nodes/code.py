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
        self.code = None
        self.key = None
        self.lang = None

    @staticmethod
    def get_from_dict(data_dict, map_list):
        return reduce(lambda d, k: d.get(k) if d else None, map_list, data_dict)

    def __call__(
        self,
        code="",
        lang='python',
        key=None,
    ):
        if key is not None:
            self.key = key
            key_list = key.split(".")
            code_dict = json.loads(code)
            return (self.get_from_dict(code_dict, key_list),)

        return (code,)


NODE_CLASS_MAPPINGS = {"Code": Code}
NODE_DISPLAY_NAME_MAPPINGS = {"Code": "Shibiko AI - Code"}
