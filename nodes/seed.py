class SeedGenerator:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "seed": ("INT", {"default": 0, "min": 0, "max": 18446744073709551615}),
            }
        }

    @classmethod
    def IS_CHANGED(cls, seed=0):
        return seed

    CATEGORY = "Shibiko AI"
    DESCRIPTION = "Share Your Seed Across Multiple Nodes."

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("SEED",)

    FUNCTION = "__call__"

    def __call__(self, seed=0):
        return (seed,)


NODE_CLASS_MAPPINGS = {"SeedGenerator": SeedGenerator}
NODE_DISPLAY_NAME_MAPPINGS = {"SeedGenerator": "Shibiko AI - Seed Generator"}
