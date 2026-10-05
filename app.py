import os
import json
import urllib.request
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# CORS সক্রিয় করা হয়েছে যাতে technographybd.xyz থেকে কোনো ব্লকিং না আসে
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route("/")
def home():
    return jsonify({
        "status": "Technography Video Downloader API Live on Render!"
    })

# --- ভিডিও ডাউনলোডার এন্ডপয়েন্ট ---
@app.route("/get-video", methods=["POST", "OPTIONS"])
def get_video():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:
        data = request.get_json(force=True, silent=True) or {}
        video_url = data.get("url", "").strip()
        mode = data.get("mode", "video")  # 'video' অথবা 'audio'

        if not video_url:
            return jsonify({"success": False, "error": "ভিডিও লিংক প্রদান করুন"}), 400

        # নির্ভরযোগ্য ব্যাকএন্ড ইঞ্জিন ক্লাস্টার
        engine_instances = [
            "https://cobalt.api.red",
            "https://api.cobalt.tools",
            "https://co.wuk.sh"
        ]

        payload = {
            "url": video_url,
            "downloadMode": "audio" if mode == "audio" else "auto",
            "videoQuality": "720",
            "audioFormat": "mp3",
            "filenameStyle": "classic"
        }
        json_payload = json.dumps(payload).encode("utf-8")

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        download_link = None
        video_title = "Technography_Downloaded_Media"

        # পর্যায়ক্রমে ক্লাস্টারগুলোতে চেষ্টা করা
        for instance in engine_instances:
            try:
                target_url = instance if instance.endswith("/") else f"{instance}/"
                req = urllib.request.Request(target_url, data=json_payload, headers=headers, method="POST")
                
                with urllib.request.urlopen(req, timeout=12) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    
                    if res_data.get("status") in ["tunnel", "redirect"]:
                        download_link = res_data.get("url")
                        video_title = res_data.get("filename", video_title)
                        break
                    elif res_data.get("status") == "picker" and res_data.get("picker"):
                        download_link = res_data["picker"][0].get("url")
                        break
                    elif res_data.get("url"):
                        download_link = res_data.get("url")
                        video_title = res_data.get("filename", video_title)
                        break
            except Exception:
                continue

        if not download_link:
            return jsonify({
                "success": False, 
                "error": "ভিডিও লিংকটি প্রসেস করা সম্ভব হয়নি। লিংকটি সঠিক কি না যাচাই করে আবার চেষ্টা করুন।"
            }), 404

        return jsonify({
            "success": True,
            "title": video_title,
            "download_url": download_link
        })

    except Exception as e:
        return jsonify({"success": False, "error": f"সার্ভার ত্রুটি: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
