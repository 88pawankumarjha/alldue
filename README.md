# Nikhil Funtime

FastAPI site for archive-backed videos.

## Current state
- Public video page at `/`
- Media comes from `archive.com`
- Video metadata will load from Firestore when credentials are present
- EC2 serves the app through nginx

## Local config
- Set `GOOGLE_APPLICATION_CREDENTIALS` or `FIREBASE_SERVICE_ACCOUNT_JSON` to the Firebase service account JSON path
- Optional: set `FIRESTORE_VIDEOS_COLLECTION` if you want a different collection name

## Run locally
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```
