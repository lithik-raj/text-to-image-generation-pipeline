# SD-Turbo Text-to-Image Generation Pipeline

A high-performance Generative AI Text-to-Image Pipeline powered by **Adversarial Diffusion Distillation (ADD)** and **SD-Turbo (`stabilityai/sd-turbo`)**, deployed on **Vercel** with real-time sub-second visual synthesis, zero rate limits, and accurate prompt-driven image generation.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/lithik-raj/text-to-image-generation-pipeline)

---

## ⚡ Pipeline Architecture & 1-Step Distillation

- **Model Checkpoint:** `stabilityai/sd-turbo`
- **Distillation Method:** Adversarial Diffusion Distillation (ADD)
- **Inference Steps:** 1 Step (`0.14s` latency benchmark)
- **Guidance Scale (CFG):** `0.0` (native single-step ADD inference)
- **Latent Resolution:** 512×512 RGB space
- **Sampler:** Euler Ancestral
- **Pipeline Components:**
  1. **CLIP ViT-L/14 NLP Encoder:** Tokenizes creative input prompts into 768-D semantic latent space.
  2. **Student UNet Predictor:** Evaluates denoised latents in a single forward pass without iterative denoising loops.
  3. **AutoencoderKL VAE Decoder:** Transforms 64×64×4 latents directly into 512×512 visual pixels.
- **Accurate Image Generation:** Direct real-time prompt-driven visual generation with zero rate-limit blocks and zero paywalls.

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
