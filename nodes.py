"""
Discord Webhook nodes (safe version: no URL stored in workflows/PNGs)

Base: Dayuppy
Mod: +message input + env/secrets for webhook URL
"""

import os
import io
import json
import tempfile
import shutil
import numpy as np
import asyncio
from PIL import Image, ImageDraw
from discord_webhook import AsyncDiscordWebhook

# === Secrets handling ===
BASE_DIR = os.path.dirname(__file__)
SECRETS_DIR = os.path.join(BASE_DIR, "secrets")
WEBHOOK_FILE = os.path.join(SECRETS_DIR, "webhook.txt")
LEGACY_FILE = os.path.join(BASE_DIR, "discord_webhook_url.txt")  # backward-compat, deprecated

def _read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""

def get_webhook_url():
    # 1) env var (recommended)
    env_url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    if env_url:
        return env_url
    # 2) local secret file
    if os.path.exists(WEBHOOK_FILE):
        return _read_file(WEBHOOK_FILE)
    # 3) legacy fallback for old setups
    if os.path.exists(LEGACY_FILE):
        return _read_file(LEGACY_FILE)
    return ""

# === Utilities ===
def create_default_image():
    """Create a simple TV test pattern image."""
    image = Image.new("RGB", (128, 128), "black")
    colors = ["white", "yellow", "cyan", "green", "magenta", "red", "blue", "black"]
    bar_width = 128 // len(colors)
    draw = ImageDraw.Draw(image)
    for i, color in enumerate(colors):
        draw.rectangle([i * bar_width, 0, (i + 1) * bar_width, 128], fill=color)
    return image

def _tensor_or_nd_to_pil_list(image):
    """
    Accepts:
      - None -> default image
      - numpy ndarray HxWxC or NxHxWxC
      - torch tensor-like with .cpu().numpy()
      - PIL.Image.Image
    Returns: list of PIL images
    """
    images_to_send = []

    if image is None:
        images_to_send.append(create_default_image())
        return images_to_send

    if isinstance(image, Image.Image):
        images_to_send.append(image)
        return images_to_send

    if isinstance(image, np.ndarray):
        if image.ndim == 4:
            for i in range(image.shape[0]):
                arr = np.clip(image[i] * 255, 0, 255).astype(np.uint8)
                images_to_send.append(Image.fromarray(arr))
        elif image.ndim == 3:
            arr = np.clip(image * 255, 0, 255).astype(np.uint8)
            images_to_send.append(Image.fromarray(arr))
        else:
            raise ValueError("Input numpy array must be 3D or 4D.")
        return images_to_send

    if hasattr(image, "cpu"):  # torch-like
        array = image.cpu().numpy()
        if array.ndim == 4:
            for i in range(array.shape[0]):
                arr = np.clip(array[i] * 255, 0, 255).astype(np.uint8)
                images_to_send.append(Image.fromarray(arr))
        elif array.ndim == 3:
            arr = np.clip(array * 255, 0, 255).astype(np.uint8)
            images_to_send.append(Image.fromarray(arr))
        else:
            raise ValueError("Input tensor must be 3D or 4D.")
        return images_to_send

    # Fallback: try to treat as PIL
    images_to_send.append(image)
    return images_to_send

def _prepare_files_for_discord(images_to_send):
    """Save PIL images to temp PNGs, enforce <20MB, return list of dicts {data, name}."""
    files = []
    temp_dir = tempfile.mkdtemp()
    try:
        for idx, img in enumerate(images_to_send):
            file_path = os.path.join(temp_dir, f"image_{idx}.png")
            img.save(file_path, format="PNG", compress_level=1)

            # if >20MB, resize and recompress
            if os.path.getsize(file_path) > 20 * 1024 * 1024:
                w, h = img.width, img.height
                img_small = img.resize((max(1, w // 2), max(1, h // 2)))
                img_small.save(file_path, format="PNG", compress_level=9)

            with open(file_path, "rb") as f:
                files.append({"data": f.read(), "name": f"image_{idx}.png"})
    finally:
        shutil.rmtree(temp_dir)
    return files

# === Nodes ===
class DiscordSetWebhook:
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("DUMMY IMAGE",)
    OUTPUT_NODE = True
    FUNCTION = "execute"
    CATEGORY = "Discord"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"URL": ("STRING",)}}

    def execute(self, URL):
        if not URL.startswith("https://discord.com/api/webhooks/"):
            raise ValueError("Invalid URL. Must start with 'https://discord.com/api/webhooks/'.")
        os.makedirs(SECRETS_DIR, exist_ok=True)
        with open(WEBHOOK_FILE, "w", encoding="utf-8") as f:
            f.write(URL.strip())
        return (create_default_image(),)

class DiscordPostViaWebhook:
    RETURN_TYPES = ("IMAGE",)
    OUTPUT_NODE = True
    FUNCTION = "execute"
    CATEGORY = "Discord"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",)
            },
            "optional": {
                "send_Message": ("BOOLEAN", {"default": False}),
                "send_Image": ("BOOLEAN", {"default": True}),
                "message": ("STRING", {"default": "", "multiline": True}),
                "prepend_message": ("STRING", {"default": "", "multiline": True}),
            },
        }

    async def _send_webhook(self, url, message, files=None):
        webhook = AsyncDiscordWebhook(url=url, content=message[:2000], timeout=30.0)
        if files:
            for file in files:
                webhook.add_file(file=file["data"], filename=file["name"])
        await webhook.execute()

    def _process_image(self, image):
        imgs = _tensor_or_nd_to_pil_list(image)
        return _prepare_files_for_discord(imgs) if imgs else None

    async def execute(self, image, send_Message=True, send_Image=True, message="", prepend_message=""):
        webhook_url = get_webhook_url()
        if not webhook_url:
            raise ValueError("Missing Discord webhook URL. Set env DISCORD_WEBHOOK_URL "
                             "or create secrets/webhook.txt")

        final_message = ""
        if send_Message:
            final_message = (prepend_message or "").strip()
            if final_message:
                final_message += "\n"
            final_message += (message or "")

        files = self._process_image(image) if send_Image else None

        if files:
            # Discord: max 10 files per message nowadays, mais on reste safe à 4
            batches = [files[i:i + 4] for i in range(0, len(files), 4)]
            for batch in batches:
                await self._send_webhook(webhook_url, final_message, batch)
        else:
            await self._send_webhook(webhook_url, final_message)

        return (image,)

class DiscordPostViaWebhookWithInput(DiscordPostViaWebhook):
    """
    Variant with connectable inputs for message/prepend (safe: no URL stored in workflow).
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "message": ("STRING", {"default": "", "multiline": True, "forceInput": True}),
            },
            "optional": {
                "send_Message": ("BOOLEAN", {"default": False}),
                "send_Image": ("BOOLEAN", {"default": True}),
                "prepend_message": ("STRING", {"default": "", "multiline": True, "forceInput": True}),
            },
        }

NODE_CLASS_MAPPINGS = {
    "DiscordSetWebhook": DiscordSetWebhook,
    "DiscordPostViaWebhook": DiscordPostViaWebhook,
    "DiscordPostViaWebhookWithInput": DiscordPostViaWebhookWithInput,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DiscordSetWebhook": "Set Discord Webhook",
    "DiscordPostViaWebhook": "Use Discord Webhook",
    "DiscordPostViaWebhookWithInput": "Use Discord Webhook (+message input)",
}
