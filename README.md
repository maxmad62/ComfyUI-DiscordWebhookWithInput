# ComfyUI-DiscordWebhookWithInput

A custom node for [ComfyUI](https://github.com/comfyanonymous/ComfyUI) that allows you to send **an image + a message (e.g. your prompt)** to a Discord channel via a webhook.  

This is based on the original Discord webhook node, with one key improvement:  
👉 you can connect a text input directly into the node (instead of only typing fixed text inside the node).

---

## ✨ Features
- Send an image and a message to a Discord webhook.
- Optional: send only text, only image, or both.
- Message input can be connected to your workflow (e.g. the same prompt you pass to CLIP).
- Handles batched images (splits into multiple messages if needed).
- Automatically resizes images >20 MB to respect Discord’s limits.
- 2000-character message limit (Discord restriction).

---

## 📦 Installation

In your `ComfyUI/custom_nodes` directory:

```bash
git clone https://github.com/maxmad62/ComfyUI-DiscordWebhookWithInput.git
