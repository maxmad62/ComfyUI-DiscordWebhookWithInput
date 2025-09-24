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

🔧 Usage

Set Discord Webhook

Add the node Set Discord Webhook and paste your Discord webhook URL.

Run it once, it will save your webhook URL locally.

Use Discord Webhook (+message input)

Add the node Use Discord Webhook (+message input).

Plug an image into image.

Plug a string (prompt, seed info, metadata…) into message.

Toggle:

send_Image = true/false

send_Message = true/false

Run the workflow

The bot posts your message and/or image in the chosen Discord channel.

📋 Notes

Make sure to install the dependency if missing:

pip install discord-webhook


(or python_embeded\python.exe -m pip install discord-webhook if using portable ComfyUI on Windows).

Discord message length is limited to 2000 characters.

Images larger than 20 MB are resized automatically.

📜 License

MIT License – feel free to use and modify.

🙌 Credits

Original base node by Dayuppy

Modifications by maxmad62 (prompt input support)
