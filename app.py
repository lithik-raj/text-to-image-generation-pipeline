import json
import os
import re
import time
import requests
from flask import Flask, jsonify, redirect, request, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=BASE_DIR)

CDN_BASE = "https://raw.githubusercontent.com/lithik-raj/text-to-image-generation-pipeline/main"
HORDE_API = "https://aihorde.net/api/v2"
HORDE_HEADERS = {
    "apikey": os.environ.get("AI_HORDE_API_KEY", "0000000000"),
    "Content-Type": "application/json",
    "User-Agent": "SDTurboPipeline/2.0",
}

AI_ART_KEYWORDS = {
    "artwork", "digital art", "illustration", "painting", "oil painting", "watercolor",
    "anime", "manga", "cartoon", "pixar", "cyberpunk", "steampunk", "fantasy", "sci-fi",
    "scifi", "futuristic", "dragon", "unicorn", "wizard", "magic", "mythical", "surreal",
    "concept art", "3d render", "cgi", "unreal engine", "neon", "synthwave", "vaporwave",
    "abstract", "sketch", "drawing", "ghibli", "van gogh", "picasso", "imaginary", "alien",
    "robot", "mecha", "nebula", "cosmos", "spacecraft", "spaceship", "planet mars",
}

REALISTIC_MODELS = [
    "ICBINP - I Can't Believe It's Not Photography",
    "Photon",
    "Reliberate",
    "Edge Of Realism",
    "Ether Real Mix",
    "Realistic Vision",
    "Deliberate 3.0",
    "AlbedoBase XL 3.1",
    "Juggernaut XL",
    "Epic Diffusion",
    "Deliberate",
    "stable_diffusion",
]

AI_ART_MODELS = [
    "Deliberate",
    "Deliberate 3.0",
    "Midjourney PaintArt",
    "Dreamlike Diffusion",
    "Project Unreal Engine 5",
    "AlbedoBase XL (SDXL)",
    "Sci-Fi Diffusion",
    "Ghibli Diffusion",
    "Epic Diffusion",
    "Rev Animated",
    "Nova Anime XL",
    "stable_diffusion",
]

_MODEL_CACHE = {"ts": 0.0, "data": {}}


def detect_generation_mode(prompt: str, requested_mode: str = "auto") -> str:
    """Resolve whether to use realistic photography or AI imaginary artwork conditioning."""
    if requested_mode in ("realistic", "ai_art"):
        return requested_mode
    lower = prompt.lower()
    for kw in AI_ART_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", lower):
            return "ai_art"
    return "realistic"


def build_horde_prompt(prompt: str, mode: str) -> str:
    """Enhance prompt gently with style cues and quality negative prompt (###)."""
    clean = (prompt or "").strip()
    if "###" in clean:
        return clean
    lower = clean.lower()
    if mode == "ai_art":
        if not re.search(r"\b(art|artwork|painting|illustration|render|anime|cartoon|sketch)\b", lower):
            clean = f"{clean}, highly detailed digital artwork, rich colors, sharp focus"
        return f"{clean} ### blurry, distorted, mutated, deformed, low quality, watermark, signature, text, worst quality"

    if not re.search(r"\b(photorealistic|photo|photography|realistic)\b", lower):
        clean = f"{clean}, natural lighting, crisp sharp focus, photorealistic"
    return f"{clean} ### blurry, distorted, mutated, deformed, extra limbs, bad anatomy, low quality, watermark, signature, text, cartoon, worst quality"


def get_active_horde_models() -> dict:
    """Fetch and briefly cache currently online AI Horde models."""
    now = time.time()
    if now - _MODEL_CACHE["ts"] < 60 and _MODEL_CACHE["data"]:
        return _MODEL_CACHE["data"]
    try:
        r = requests.get(f"{HORDE_API}/status/models?type=image", headers={"User-Agent": "SDTurboPipeline/2.0"}, timeout=4)
        if r.ok:
            data = {m["name"]: m for m in r.json() if m.get("count", 0) >= 1}
            _MODEL_CACHE["ts"] = now
            _MODEL_CACHE["data"] = data
            return data
    except Exception:
        pass
    return _MODEL_CACHE["data"]


def pick_horde_models(mode: str) -> list[str]:
    """Select active, fast AI Horde models tailored to realistic or AI artwork mode."""
    preferred = AI_ART_MODELS if mode == "ai_art" else REALISTIC_MODELS
    active = get_active_horde_models()
    if not active:
        return preferred[:4]

    avail = [m for m in preferred if m in active and m != "stable_diffusion"]
    # Prefer fast active multi-worker checkpoints while filtering out extreme long-queue stalls
    avail.sort(key=lambda m: (0 if active[m].get("eta", 999) <= 150 else 1, -min(active[m].get("count", 1), 4), active[m].get("eta", 999)))
    if not avail:
        return ["ICBINP - I Can't Believe It's Not Photography", "Deliberate", "stable_diffusion"]
    if len(avail) < 3 and "stable_diffusion" in active:
        avail.append("stable_diffusion")
    return avail[:5]


def submit_horde_job(prompt: str, n_images: int = 4, steps: int = 4, seed=None, mode: str = "auto"):
    """Submit a non-blocking diffusion job to AI Horde."""
    resolved_mode = detect_generation_mode(prompt, mode)
    full_prompt = build_horde_prompt(prompt, resolved_mode)
    models = pick_horde_models(resolved_mode)
    mapped_steps = {1: 14, 2: 16, 3: 18, 4: 20}.get(int(steps), 18)

    params = {
        "width": 512,
        "height": 512,
        "steps": mapped_steps,
        "cfg_scale": 7.0,
        "sampler_name": "k_euler_a",
        "n": max(1, min(int(n_images), 8)),
    }
    if seed is not None and str(seed).strip() != "":
        params["seed"] = str(seed).strip()

    payload = {
        "prompt": full_prompt,
        "params": params,
        "models": models,
        "nsfw": False,
        "censor_nsfw": True,
        "r2": True,
    }
    r = requests.post(f"{HORDE_API}/generate/async", json=payload, headers=HORDE_HEADERS, timeout=10)
    if r.status_code == 403:
        # Retry with slimmer batch/steps if anonymous kudos budget exceeded
        payload["params"]["n"] = min(params["n"], 4)
        payload["params"]["steps"] = 14
        r = requests.post(f"{HORDE_API}/generate/async", json=payload, headers=HORDE_HEADERS, timeout=10)
    r.raise_for_status()
    return r.json().get("id"), resolved_mode, models


def call_gradio_sync(base_url: str, endpoint: str, data: list, timeout: int = 12):
    """Invoke a Hugging Face Gradio Space synchronously within short serverless time budget."""
    r = requests.post(f"{base_url}/gradio_api/call{endpoint}", json={"data": data}, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
    r.raise_for_status()
    ev = r.json().get("event_id")
    if not ev:
        return None
    r2 = requests.get(f"{base_url}/gradio_api/call{endpoint}/{ev}", headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout)
    r2.raise_for_status()
    last_event = ""
    for line in r2.text.splitlines():
        if line.startswith("event:"):
            last_event = line.split(":", 1)[1].strip()
        elif last_event == "complete" and line.startswith("data:"):
            parsed = json.loads(line[5:].strip())
            if isinstance(parsed, list) and parsed:
                item = parsed[0]
                if isinstance(item, dict) and item.get("url"):
                    return item["url"]
                if isinstance(item, list) and item and isinstance(item[0], dict):
                    img_obj = item[0].get("image") or item[0]
                    if isinstance(img_obj, dict) and img_obj.get("url"):
                        return img_obj["url"]
    return None


@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/<filename>")
def serve_file(filename):
    if filename.endswith((".png", ".jpg", ".jpeg", ".ico", ".svg", ".webp")):
        for folder in (BASE_DIR, os.path.join(BASE_DIR, "public"), os.path.join(BASE_DIR, "api")):
            target = os.path.join(folder, filename)
            if os.path.exists(target):
                return send_from_directory(folder, filename)
        return redirect(f"{CDN_BASE}/{filename}")
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/health")
def health():
    return jsonify({
        "status": "online",
        "service": "SD-Turbo & Hybrid Diffusion Text-to-Image Pipeline",
        "primary_engines": [
            "Z-Image-Turbo",
            "FLUX.1-schnell",
            "SD3.5-Large-Turbo",
            "stabilityai/sd-turbo",
            "AI Horde Diffusion Cluster",
        ],
        "capabilities": ["photorealistic", "ai_imaginary", "digital_artwork", "unlimited_failover"],
        "interface": "Gradio Web UI (Soft Theme)",
    })


@app.route("/api/horde/start", methods=["POST"])
def horde_start():
    body = request.get_json(silent=True) or {}
    prompt = (body.get("prompt") or "a dog playing with a ball at beach").strip()
    n_images = int(body.get("n_images") or 4)
    steps = int(body.get("steps") or 4)
    seed = body.get("seed")
    mode = body.get("mode") or "auto"

    try:
        job_id, resolved_mode, models = submit_horde_job(prompt, n_images, steps, seed, mode)
        return jsonify({
            "success": True,
            "job_id": job_id,
            "mode": resolved_mode,
            "models": models,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 502


@app.route("/api/horde/status/<job_id>", methods=["GET"])
def horde_status(job_id):
    try:
        chk_res = requests.get(f"{HORDE_API}/generate/check/{job_id}", headers={"User-Agent": "SDTurboPipeline/2.0"}, timeout=6)
        chk_res.raise_for_status()
        chk = chk_res.json()
        if not chk.get("done") and not chk.get("faulted"):
            return jsonify({
                "done": False,
                "faulted": False,
                "wait_time": chk.get("wait_time", 0),
                "queue_position": chk.get("queue_position", 0),
                "finished": chk.get("finished", 0),
                "processing": chk.get("processing", 0),
                "waiting": chk.get("waiting", 0),
            })

        st_res = requests.get(f"{HORDE_API}/generate/status/{job_id}", headers={"User-Agent": "SDTurboPipeline/2.0"}, timeout=8)
        st_res.raise_for_status()
        st = st_res.json()
        gens = st.get("generations", [])
        images = [g["img"] for g in gens if g.get("img")]
        models_used = list({g.get("model", "Diffusion") for g in gens if g.get("model")})
        return jsonify({
            "done": True,
            "faulted": bool(chk.get("faulted")) and not images,
            "images": images,
            "model": ", ".join(models_used) if models_used else "AI Horde Diffusion",
        })
    except Exception as e:
        return jsonify({"done": False, "error": str(e)}), 200


@app.route("/api/generate", methods=["GET", "POST"])
def generate():
    """Synchronous generation API for external HTTP callers."""
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or request.args.get("prompt") or "a dog playing with a ball at beach").strip()
    n_images = max(1, min(int(data.get("n_images") or request.args.get("n_images") or 1), 4))
    steps = int(data.get("steps") or request.args.get("steps") or 4)
    seed_raw = data.get("seed") if "seed" in data else request.args.get("seed", 1000)
    seed = int(seed_raw) if str(seed_raw).isdigit() else 1000
    mode = (data.get("mode") or request.args.get("mode") or "auto").strip()

    resolved_mode = detect_generation_mode(prompt, mode)
    prompt_text = build_horde_prompt(prompt, resolved_mode).split("###")[0].strip()

    # Try fast HF Gradio Space within Vercel time budget
    z_steps = min(max(steps + 4, 5), 8)
    try:
        url = call_gradio_sync("https://mrfakename-z-image-turbo.hf.space", "/generate_image", [prompt_text, 512, 512, z_steps, seed, False], timeout=8)
        if url:
            return jsonify({"success": True, "prompt": prompt, "mode": resolved_mode, "images": [url], "model": "Z-Image-Turbo"})
    except Exception:
        pass

    try:
        job_id, resolved_mode, models = submit_horde_job(prompt, n_images, steps, seed, mode)
        return jsonify({
            "success": True,
            "async": True,
            "job_id": job_id,
            "status_url": f"/api/horde/status/{job_id}",
            "prompt": prompt,
            "mode": resolved_mode,
            "models": models,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
