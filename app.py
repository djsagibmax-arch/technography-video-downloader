import os
import io
import base64
import urllib.parse
import urllib.request
import json
import random
from flask import Flask, request, jsonify
from flask_cors import CORS
from huggingface_hub import InferenceClient
import yt_dlp

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Hugging Face Inference Client
HF_TOKEN = os.environ.get("HF_TOKEN")
client = InferenceClient(api_key=HF_TOKEN)

def translate_to_english(text):
    """স্বয়ংক্রিয় ভাষা অনুবাদ"""
    try:
        encoded_text = urllib.parse.quote(text)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q={encoded_text}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode('utf-8'))
            return "".join([part[0] for part in result[0] if part[0]])
    except Exception as e:
        print(f"Translation Error: {e}")
        return text

@app.route("/")
def home():
    return jsonify({"status": "Technography Backend (AI + Video) Live on Render!"})

# --- ১. AI ইমেজ জেনারেটর এন্ডপয়েন্ট ---
@app.route("/generate", methods=["POST", "OPTIONS"])
def generate():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:
        data = request.get_json(force=True, silent=True) or {}
        user_prompt = data.get("prompt", "").strip()
        seed = data.get("seed")
        
        if seed is None:
            seed = random.randint(1, 999999999)
        else:
            seed = int(seed)

        if not user_prompt:
            return jsonify({"success": False, "error": "প্রম্পট খালি রাখা যাবে না"}), 400

        english_prompt = translate_to_english(user_prompt)
        enhanced_prompt = f"{english_prompt}, cinematic, photorealistic, sharp focus, 8k resolution"

        image = client.text_to_image(
            prompt=enhanced_prompt,
            model="black-forest-labs/FLUX.1-schnell",
            seed=seed
        )

        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=90)
        img_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return jsonify({
            "success": True,
            "image": f"data:image/jpeg;base64,{img_b64}",
            "seed": seed
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# --- ২. ভিডিও ডাউনলোডার এন্ডপয়েন্ট ---
@app.route("/get-video", methods=["POST", "OPTIONS"])
def get_video():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:
        data = request.get_json(force=True, silent=True) or {}
        video_url = data.get("url", "").strip()

        if not video_url:
            return jsonify({"success": False, "error": "ভিডিও লিংক প্রদান করুন"}), 400

        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            title = info.get('title', 'Video')
            thumbnail = info.get('thumbnail', '')
            download_url = info.get('url', '')

            # কিছু প্ল্যাটফর্মের ক্ষেত্রে formats লিস্ট চেক করা
            if not download_url and 'formats' in info:
                for f in reversed(info['formats']):
                    if f.get('url'):
                        download_url = f['url']
                        break

            if not download_url:
                return jsonify({"success": False, "error": "ভিডিও ডাউনলোড লিংক পাওয়া যায়নি"}), 404

            return jsonify({
                "success": True,
                "title": title,
                "thumbnail": thumbnail,
                "download_url": download_url
            })
    except Exception as e:
        return jsonify({"success": False, "error": f"ত্রুটি: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
