## Shibiko AI ComfyUI Tools

### What is this?
This is a collection of tools that I use to make my life easier when developing ComfyUI applications. Waifu2x to reduce noise and upscale 2x and 4x trained on art or phones. Luts used in the photo and film industry to recolor images. I use this tools to further develop features for [Shibiko AI](https://shibiko.ai)

### Notes
I put in credits for the original creators of the underlining tools that I use to create nodes. So links in each section are for each creator, repo, and patreon if they have one.

### Waifu2x
This tool is a simple wrapper around the waifu2x command line tool. It allows you to upscale images and remove noise using the waifu2x ai model. It produces high quality upscaled images that are suitable for use in ComfyUI applications.

Credits: [Nagadomi](https://github.com/nagadomi) |
[GitHub](https://github.com/nagadomi/nunif) |
[Pateron](https://patreon.com/nagadomi)

![waifu2x-preview](https://github.com/Shibiko-AI/ShibikoAI-ComfyUI-Tools/assets/5192788/b690bc79-f377-4ef8-8f6c-d468fcdb0894)

### Luts
I wrote this using built in methods from the PIL library and converting the image types. This comes straight from production code I use in [Shibiko AI](https://shibiko.ai).
If you have any issues, please check to make sure that you have a luts directory in the models directory with luts in it.

Default Luts come from [on1.com](https://www.on1.com/free/luts/all-luts/) selected a few of the free ones to use in this tool. Please go to the site and check out the rest of the free luts.

![luts-preview](https://github.com/Shibiko-AI/ShibikoAI-ComfyUI-Tools/assets/5192788/5e564dde-f8b4-40cb-ae4f-6c26603ff0ca)
