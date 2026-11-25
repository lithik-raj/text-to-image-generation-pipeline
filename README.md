# SD-Turbo Real-Time Text-to-Image Generation Studio

A high-performance Generative AI Text-to-Image Studio powered by **Adversarial Diffusion Distillation (ADD)** and **SD-Turbo**, deployed as a zero-latency web application on **Vercel**.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/lithik-raj/text-to-image-generation-pipeline)

---

## ⚡ What Makes This Special

- **Real Dynamic Generation:** Generates real, unique, high-resolution visuals for ANY custom user prompt in real-time.
- **Fine-Tuning Style Engine:**
  - 🌟 **Photorealistic Ultra-HD:** Fine-tuned for 8K textures, 35mm DSLR depth of field, and natural cinematic lighting.
  - 🎨 **Anime & Manga Art:** Fine-tuned for vibrant colors, Makoto Shinkai aesthetic, and clean lineart.
  - 🎬 **Cinematic Masterpiece:** Fine-tuned for anamorphic lens flair, atmospheric volumetric mist, and dramatic film stills.
  - 🔮 **Cyberpunk & Sci-Fi:** Fine-tuned for neon glows, futuristic reflections, and octane renders.
  - 🖌️ **Fantasy Concept Art:** Fine-tuned for painterly brushstrokes and ArtStation trending quality.
- **Streamlined Creative Workflow:** Removed cryptic CFG sliders and confusing technical steps in favor of intuitive prompt engineering, aspect ratio selection, seed randomization, and 1-click downloads.
- **Session History Gallery:** Keep track of all creations during your session and click back to inspect or download any previous image.

---

## 🚀 Live Demo & Repository

- **Live Production App:** [https://text-to-image-generation-pipeline.vercel.app](https://text-to-image-generation-pipeline.vercel.app)
- **GitHub Repository:** [https://github.com/lithik-raj/text-to-image-generation-pipeline](https://github.com/lithik-raj/text-to-image-generation-pipeline)

---

## 🛠️ Local Development & Running the Pipeline

```bash
# 1. Clone repository
git clone https://github.com/lithik-raj/text-to-image-generation-pipeline.git
cd text-to-image-generation-pipeline

# 2. Install requirements
pip install -r requirements.txt

# 3. Start local development server
python app.py
```

For full GPU pipeline execution with PyTorch and Diffusers, install `requirements-gpu.txt` and launch `Text_to_Image_Pretrained_FAST.ipynb`.
