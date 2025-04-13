class BboxSplit:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "bbox": ("BBOX",),
            }
        }

    CATEGORY = "Shibiko AI"
    DESCRIPTION = "Split a BBOX into x, y, width, height."

    RETURN_TYPES = ("INT", "INT", "INT", "INT")
    RETURN_NAMES = ("x", "y", "width", "height")

    FUNCTION = "__call__"

    def __call__(self, bbox):
        x, y, width, height = bbox[0]
        return x, y, width, height,


NODE_CLASS_MAPPINGS = {"BboxSplit": BboxSplit}
NODE_DISPLAY_NAME_MAPPINGS = {"BboxSplit": "Shibiko AI - BBOX Split"}
