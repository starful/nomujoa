# 🇰🇷 Nomujoa (K-POP Cheering Board Maker)

**Nomujoa** (derived from the Korean phrase "너무 좋아" meaning "I like it so much") is a web application designed for global K-POP fans. It empowers users to create professional-grade concert slogans, LED boards, and "Uchiwas" (fans) using authentic Korean fandom slang, even without knowing the language.

Unlike simple translators, Nomujoa leverages **Google Gemini 2.0 Flash** to understand specific idol personas, nicknames, and memes, converting simple phrases like "I love you" into deep fandom slang (e.g., "Borahae" for BTS, "Horanghae" for Seventeen).

🌐 **Live Site:** [nomujoa.com](https://nomujoa.com)

---

## ✨ Key Features

### 1. 🤖 AI-Powered "Fandom Slang" Translation
- **Context-Aware Translation:** Converts generic messages into authentic Korean fandom slang based on the selected artist.
- **Member-Specific Personas:** Recognizes specific nicknames and memes for major groups (BTS, SEVENTEEN, TWICE, IVE, NewJeans, etc.).
- **Hybrid Data System:** Uses pre-generated JSON cache for speed and falls back to **Google Gemini 2.0 Flash** for custom requests.

### 2. 🔍 Smart Search & Multi-Language Support
- **Smart Search:** Instantly find groups or members by typing their names (e.g., Type "Hoshi" → Finds "SEVENTEEN").
- **Global UI:** Fully supports English, Japanese, Korean, and Chinese interfaces.

### 3. 🎨 Interactive Visual Editor
- **Canvas Editor:** Built with **Fabric.js** for drag-and-drop editing.
- **Rich Assets:** Trendy backgrounds (Galaxy, Hologram, Check) and vector stickers.
- **Auto-Color:** Automatically suggests the idol group's official colors.
- **Portrait/Landscape Mode:** Switch between Uchiwa (fan) and Slogan (board) layouts.

---

## 🛠️ Tech Stack

- **Backend:** Python 3.10, Flask (Blueprint structure)
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla), Fabric.js
- **AI Model:** Google Gemini 2.0 Flash (via `google-generativeai`)
- **Infrastructure:** Google Cloud Run, Cloud Build, Artifact Registry, Docker
- **Server:** Gunicorn

---

## 📂 Project Structure

Refactored for scalability and maintenance.

```text
nomujoa/
├── app/
│   ├── __init__.py          # Flask App Factory & Config
│   ├── routes.py            # URL Routes (Blueprints)
│   ├── utils.py             # Data loading & helper functions
│   ├── gemini_client.py     # AI Logic & Prompt Engineering
│   ├── static/              # CSS, JS, Images
│   └── templates/           # HTML Templates
├── data/                    # Data Storage
│   ├── dicts/               # Pre-generated AI Slang JSONs
│   ├── raw/                 # Source CSVs
│   ├── wiki/                # Markdown Wiki Posts
│   ├── groups.json          # Group Metadata
│   ├── translations.json    # UI Translation Strings
│   └── phrase_mapping.json  # Intent Mapping
├── scripts/                 # Utility Scripts
│   ├── batch_generator.py   # Pre-generate slang data
│   └── generate_wiki.py     # Generate Wiki content via AI
├── config.py                # Centralized Configuration
├── Dockerfile               # Container Configuration
├── requirements.txt         # Python Dependencies
└── cloudbuild.yaml          # CI/CD Configuration
```

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

Create a `.env` file in the root directory:

```ini
GEMINI_API_KEY=your_google_gemini_api_key_here
PORT=8080
```

### 5. Generate Data (Optional)

Run the batch generator to create the JSON cache files for faster responses.

```bash
python scripts/batch_generator.py
```

### 6. Run the Server

Since `run.py` has been removed for optimization, use the standard Flask command:

```bash
# Linux/Mac
export FLASK_APP=app
flask run --port=8080

# Windows (CMD)
set FLASK_APP=app
flask run --port=8080

# Windows (PowerShell)
$env:FLASK_APP = "app"
flask run --port=8080
```

Visit `http://localhost:8080` in your browser.

---

## ☁️ Deployment (Google Cloud Run)

This project is configured for automated deployment using **Google Cloud Build**.

### Build and Deploy

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