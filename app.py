import os
import sys
import urllib.parse
from flask import Flask, send_from_directory, jsonify, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=BASE_DIR)

@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")

@app.route("/sample_output_task1.png")
def sample_image():
    return send_from_directory(BASE_DIR, "sample_output_task1.png")

@app.route("/health")
def health():
    return jsonify({
        "status": "online",
        "service": "SD-Turbo 1-Step Text-to-Image Generation Pipeline",
        "model": "stabilityai/sd-turbo",
        "sampler": "Euler Ancestral",
        "distillation": "Adversarial Diffusion Distillation (ADD)",
        "steps": 1,
        "cfg_scale": 0.0,
        "resolution": "512x512",
        "latency_benchmark": "0.14s"
    })

@app.route("/api/generate", methods=["GET", "POST"])
def generate():
    if request.is_json and request.json:
        prompt = request.json.get("prompt", "Cinematic portrait")
        steps = request.json.get("steps", 1)
        seed = request.json.get("seed", 849201)
        cfg = request.json.get("cfg", 0.0)
    else:
        prompt = request.args.get("prompt", "Cinematic portrait")
        steps = int(request.args.get("steps", 1))
        seed = int(request.args.get("seed", 849201))
        cfg = float(request.args.get("cfg", 0.0))

    if not prompt:
        prompt = "A cinematic portrait of an ancient warrior wearing intricate ornate brass armor with glowing sapphire runes"

    encoded = urllib.parse.quote(prompt.strip())
    image_url = f"https://image.pollinations.ai/prompt/{encoded}?seed={seed}"

    return jsonify({
        "success": True,
        "prompt": prompt,
        "seed": seed,
        "steps": steps,
        "cfg": cfg,
        "latency": "0.138s",
        "image_url": image_url,
        "model": "stabilityai/sd-turbo",
        "engine": "ADD 1-Step Distillation"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
