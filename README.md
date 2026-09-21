# BhoomiIntelli OCR Service

FastAPI + PaddleOCR microservice for extracting land record data from scanned documents.

## Tech Stack

- **Framework:** FastAPI (Python 3.10)
- **OCR Engine:** PaddleOCR v2.7 (Hindi + English, angle-correction enabled)
- **Container:** Docker (for deployment on Render / Railway / Fly.io)

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/ocr/health` | Health check |
| `GET` | `/api/records` | List all extracted records |
| `POST` | `/api/records` | Create or update a record |
| `POST` | `/api/ocr/extract` | Upload image/PDF → get structured land record JSON |

### POST `/api/ocr/extract`

**Request:** `multipart/form-data`
- `document` — image file (JPG, PNG, etc.)
- `hint` *(optional)* — document type hint (e.g. `"khasra"`, `"7-12"`)

**Response:**
```json
{
  "success": true,
  "data": {
    "khasraNumber": "123/4",
    "ownerName": "Ramesh Kumar",
    "area": "2.5 Hectares",
    "landType": "Agricultural",
    "district": "Jaipur",
    "tehsil": "Sanganer",
    "state": "Rajasthan",
    "village": "Phagi",
    "taxAmount": "",
    "raw_text": "..."
  },
  "meta": {
    "originalFilename": "khasra.jpg",
    "totalTimeMs": 1240
  }
}
```

## Local Development

```bash
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
source venv/bin/activate  # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment config
cp .env.example .env

# 4. Run dev server
python main.py
# → http://localhost:8000
```

## Deployment (Render)

1. Push this folder to a GitHub repository.
2. Go to [render.com](https://render.com) → **New +** → **Web Service**.
3. Connect your GitHub repo.
4. Set **Runtime** to **Docker** (auto-detected from `Dockerfile`).
5. Under **Environment Variables**, add:
   ```
   ALLOWED_ORIGINS=https://your-admin-portal.vercel.app,https://your-user-portal.vercel.app
   ```
6. Click **Create Web Service** and wait ~5 minutes for the first build.
7. Copy the public URL (e.g. `https://bhoomi-ocr.onrender.com`).

## Connecting to Vercel Frontends

In your Vercel dashboard for both **Admin Portal** and **User Portal**:
- **Settings → Environment Variables**
- Add: `VITE_API_BASE_URL` = `https://bhoomi-ocr.onrender.com`
- Click **Redeploy**
