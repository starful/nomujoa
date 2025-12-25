### 📝 README.md

````markdown
# 🇰🇷 Nomujoa (K-POP Cheering Board Maker)

**Nomujoa** (derived from the Korean phrase "너무 좋아" meaning "I like it so much") is a web application designed for global K-POP fans. It empowers users to create professional-grade concert slogans, LED boards, and "Uchiwas" (fans) using authentic Korean fandom slang, even without knowing the language.

Unlike simple translators, Nomujoa leverages **Google Gemini 2.0 Flash** to understand specific idol personas, nicknames, and memes, converting simple phrases like "I love you" into deep fandom slang (e.g., "Borahae" for BTS, "Horanghae" for Seventeen).

🌐 **Live Site:** [nomujoa.com](https://nomujoa.com)

---

## ✨ Key Features

### 1. 🤖 AI-Powered "Fandom Slang" Translation

- **Context-Aware Translation:** Converts generic messages into authentic Korean fandom slang.
  - _Input:_ "I love you" (to SEVENTEEN Hoshi) → _Output:_ "Horanghae 🐯" (Tiger + I love you)
- **Member-Specific Personas:** The AI recognizes specific nicknames and memes for major groups including BTS, SEVENTEEN, TWICE, IVE, NewJeans, and more.
- **Google Gemini 2.0 Flash:** Utilizes the latest high-performance model to capture subtle nuances of the Korean language and internet culture.

### 2. ⚡ Hybrid Data System (Cost & Speed Optimization)

- **Pre-generated JSON Cache:** Frequently used phrases and member-specific slogans are pre-generated using a batch script (`batch_generator.py`) and stored as JSON files. This ensures **zero latency** and **zero API cost** for 90% of common requests.
- **Real-time AI Fallback:** If a user inputs a unique or custom phrase, the system seamlessly falls back to the Gemini API to generate fresh slogans in real-time.

### 3. 🎨 Interactive Visual Editor

- **Canvas Editor:** Built with **Fabric.js**, allowing users to drag, drop, resize, and rotate text and stickers.
- **Rich Assets:**
  - **Backgrounds:** Trendy templates like Check patterns, Galaxy, Hologram, and Dark Chic.
  - **Stickers:** High-quality vector assets including animals, ribbons, hearts, and hand signs.
  - **Official Colors:** Automatically suggests the idol group's official colors upon selection.
- **Typography:** Uses high-visibility Korean fonts (e.g., Gmarket Sans) optimized for concert visibility.

### 4. 📱 Mobile-First Design

- Fully responsive UI optimized for smartphone browsers.
- Supports switching between **Portrait Mode** (for Uchiwa fans) and **Landscape Mode** (for Slogans/LED boards).

---

## 🛠️ Tech Stack

- **Backend:** Python 3.10, Flask
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla), Fabric.js
- **AI Model:** Google Gemini 2.0 Flash (via `google-generativeai`)
- **Infrastructure:** Google Cloud Run, Cloud Build, Artifact Registry, Docker
- **Server:** Gunicorn

---

## 📂 Project Structure

```text
nomujoa/
├── app/
│   ├── __init__.py          # Flask App Factory & Routes
│   ├── gemini_client.py     # AI Logic & Prompt Engineering
│   ├── data/
│   │   ├── phrase_mapping.json # Intent mapping for quick phrases
│   │   └── dicts/           # Pre-generated JSON Data (BTS.json, etc.)
│   ├── static/
│   │   ├── css/             # Stylesheets
│   │   ├── js/              # Frontend Logic (main.js, canvas.js, data.js)
│   │   └── images/          # Assets (Stickers, Templates)
│   └── templates/           # HTML Templates
├── batch_generator.py       # Script to pre-generate slang JSONs
├── requirements.txt         # Python Dependencies
├── Dockerfile               # Container Configuration
├── cloudbuild.yaml          # CI/CD Configuration for Google Cloud
└── run.py                   # Local Development Entry Point
```
````

---

## 🚀 Getting Started (Local Development)

### 1. Clone the repository

```bash
git clone https://github.com/your-username/nomujoa.git
cd nomujoa
```

### 2. Set up Virtual Environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory and add your Google Gemini API Key:

```ini
GEMINI_API_KEY=your_google_gemini_api_key_here
```

### 5. Generate Data (Optional but Recommended)

Run the batch generator to create the JSON cache files for faster responses.

```bash
python batch_generator.py
```

### 6. Run the Server

```bash
python run.py
```

Visit `http://localhost:8080` in your browser.

---

## ☁️ Deployment (Google Cloud Run)

This project is configured for automated deployment using **Google Cloud Build**.

### 1. Create Artifact Registry Repository (One-time setup)

```bash
gcloud artifacts repositories create nomujoa-repo \
    --repository-format=docker \
    --location=us-central1 \
    --description="Repository for Nomujoa App"
```

### 2. Build and Deploy

Run the following command to build the Docker image and deploy it to Cloud Run.
_(Replace `YOUR_API_KEY` with your actual Gemini API key)_

```bash
gcloud builds submit \
    --substitutions=_GEMINI_API_KEY="YOUR_ACTUAL_API_KEY"
```

---

## 📝 License

This project is created for educational and service purposes.
Sticker assets and fonts used may have their own licenses.

---

**Made with ❤️ for K-POP Fans.**

```

```
