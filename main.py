"""Nikhil Funtime — FastAPI app for archive-backed videos."""

from __future__ import annotations

import os
from typing import Any

from datetime import datetime

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = os.path.dirname(__file__)
DEFAULT_FIRESTORE_COLLECTION = "videos"
DEFAULT_FIRESTORE_DEV_COLLECTION = "dev_videos"
DEFAULT_FIRESTORE_DATABASE = "default"
BASE_PATH = os.environ.get("BASE_PATH", "").rstrip("/")
STATIC_PATH = f"{BASE_PATH}/static" if BASE_PATH else "/static"
HOME_PATH = f"{BASE_PATH}/" if BASE_PATH else "/"

app = FastAPI()
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
if BASE_PATH:
    app.mount(f"{BASE_PATH}/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static-dev")


def _credentials_path() -> str | None:
    return os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")


def _load_firestore_client():
    credentials_path = _credentials_path()
    if not credentials_path or not os.path.exists(credentials_path):
        return None

    try:
        from google.cloud import firestore

        return firestore.Client.from_service_account_json(
            credentials_path,
            database=os.environ.get("FIRESTORE_DATABASE_ID", DEFAULT_FIRESTORE_DATABASE),
        )
    except Exception:
        return None


def _firestore_module():
    from google.cloud import firestore

    return firestore


def _normalize_video(document: dict[str, Any], doc_id: str) -> dict[str, Any]:
    quality_options = document.get("qualityOptions") or document.get("quality_options") or []
    published = document.get("published", document.get("publishStatus", True))
    return {
        "id": document.get("id") or doc_id,
        "title": document.get("title") or "Untitled",
        "creator": document.get("creator") or "Nikhil Funtime",
        "duration": document.get("duration") or "",
        "views": document.get("views") or document.get("viewCount") or "0 views",
        "summary": document.get("summary") or document.get("description") or "",
        "archive_url": document.get("archive_url") or document.get("archiveVideoUrl") or "",
        "video_url": document.get("video_url") or document.get("archiveVideoUrl") or "",
        "quality_options": quality_options,
        "thumb_url": document.get("thumb_url") or document.get("archiveThumbUrl") or "",
        "published": bool(published),
        "tags": document.get("tags") or [],
        "viewCount": int(document.get("viewCount") or 0),
        "commentCount": int(document.get("commentCount") or 0),
        "subscriberCount": int(document.get("subscriberCount") or 0),
        "likeCount": int(document.get("likeCount") or 0),
    }


def _collection_name_for_request(request: Request) -> str:
    return DEFAULT_FIRESTORE_DEV_COLLECTION if request.url.path.startswith("/dev/") else DEFAULT_FIRESTORE_COLLECTION


def _dev_collection_name() -> str:
    return DEFAULT_FIRESTORE_DEV_COLLECTION


def _prod_collection_name() -> str:
    return DEFAULT_FIRESTORE_COLLECTION


def load_videos_from_firestore(request: Request) -> tuple[list[dict[str, Any]], bool]:
    client = _load_firestore_client()
    if client is None:
        print("Firestore connected: false")
        return [], False

    try:
        collection_name = os.environ.get("FIRESTORE_DEV_VIDEOS_COLLECTION" if request.url.path.startswith("/dev/") else "FIRESTORE_VIDEOS_COLLECTION", _collection_name_for_request(request))
        db_name = os.environ.get("FIRESTORE_DATABASE_ID", DEFAULT_FIRESTORE_DATABASE)
        docs = client.collection(collection_name).stream()
        videos = []
        for doc in docs:
            data = doc.to_dict() or {}
            video = _normalize_video(data, doc.id)
            if video["published"]:
                videos.append(video)
        if videos:
            print(f"Firestore connected: true database={db_name} collection={collection_name} videos={len(videos)}")
            return videos, True
    except Exception:
        print("Firestore connected: false")

    print("Firestore connected: false")
    return [], False


def search_archive_videos(videos: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    terms = query.strip().lower().split()
    if not terms:
        return videos

    results = []
    for video in videos:
        haystack = " ".join(
            [
                video["title"],
                video["creator"],
                video["summary"],
                video["id"],
                " ".join(video.get("tags", [])),
            ]
        ).lower()
        if all(term in haystack for term in terms):
            results.append(video)
    return results


def _paths_for_request(request: Request) -> dict[str, str]:
    base_path = "/dev" if request.url.path.startswith("/dev/") else ""
    return {
        "base_path": base_path,
        "home_path": f"{base_path}/" if base_path else "/",
        "static_path": f"{base_path}/static" if base_path else "/static",
    }


def render_video_page(request: Request, v: str = "", q: str = ""):
    all_videos, firestore_ready = load_videos_from_firestore(request)
    path_context = _paths_for_request(request)
    if not all_videos:
        return templates.TemplateResponse(
            "videos.html",
            {
                "request": request,
                "selected": None,
                "recommendations": [],
                "videos": [],
                "query": q.strip(),
                "has_results": False,
                "firestore_ready": firestore_ready,
                "firestore_empty": True,
                "public_actions_enabled": request.url.path.startswith("/dev/"),
                **path_context,
            },
        )

    query = q.strip()
    filtered_videos = search_archive_videos(all_videos, query)
    visible_videos = filtered_videos or all_videos
    selected = next((video for video in visible_videos if video["id"] == v), visible_videos[0])
    recommendations = [video for video in visible_videos if video["id"] != selected["id"]]
    source = "firestore" if firestore_ready else "fallback"
    print(f"render_video_page source={source} selected={selected['id']} query={query or '-'}")
    return templates.TemplateResponse(
        "videos.html",
        {
            "request": request,
            "selected": selected,
            "recommendations": recommendations,
            "videos": filtered_videos,
            "query": query,
            "has_results": bool(filtered_videos),
            "firestore_ready": firestore_ready,
            "firestore_empty": False,
            "public_actions_enabled": request.url.path.startswith("/dev/"),
            **path_context,
        },
    )


def _get_video_doc(video_id: str):
    raise RuntimeError("Use _get_video_doc_for_request")


def _get_video_doc_for_request(request: Request, video_id: str):
    client = _load_firestore_client()
    if client is None:
        return None
    collection_name = _collection_name_for_request(request)
    return client.collection(collection_name).document(video_id)


def _seed_if_missing(collection_name: str, video: dict[str, Any]):
    client = _load_firestore_client()
    if client is None:
        return
    doc = client.collection(collection_name).document(video["id"])
    if doc.get().exists:
        return
    doc.set(video)


def _base_video_doc() -> dict[str, Any]:
    return {
        "id": "suno-darwaza-mat-kholna",
        "title": "Suno Darwaza Mat Kholna",
        "creator": "Nikhil Funtime",
        "duration": "3:22",
        "views": "New Archive upload",
        "summary": "A suspenseful horror short video from Nikhil Funtime.",
        "description": "A suspenseful horror short video from Nikhil Funtime.",
        "archive_url": "https://archive.org/details/suno-darwaza-mat-kholna",
        "archiveVideoUrl": "https://archive.org/download/suno-darwaza-mat-kholna/Project_05-11_Full%20HD%201080p_MEDIUM_FR30_%282%29.ia.mp4",
        "archiveThumbUrl": "https://archive.org/download/suno-darwaza-mat-kholna/1778528528940.png",
        "qualityOptions": [
            {
                "label": "Fast 480p",
                "url": "https://archive.org/download/suno-darwaza-mat-kholna/Project_05-11_Full%20HD%201080p_MEDIUM_FR30_%282%29.ia.mp4",
            },
            {
                "label": "HD 1080p",
                "url": "https://archive.org/download/suno-darwaza-mat-kholna/Project_05-11_Full%20HD%201080p_MEDIUM_FR30_%282%29.mp4",
            },
        ],
        "thumb_url": "https://archive.org/download/suno-darwaza-mat-kholna/1778528528940.png",
        "published": True,
        "tags": ["horror", "archive"],
        "viewCount": 0,
        "commentCount": 0,
        "subscriberCount": 0,
        "likeCount": 0,
    }


@app.on_event("startup")
def startup_seed_dev():
    if os.environ.get("APP_ENV", "dev").lower() == "dev":
        _seed_if_missing(_dev_collection_name(), _base_video_doc())


@app.post("/videos/{video_id}/like")
@app.post("/dev/videos/{video_id}/like")
def like_video(request: Request, video_id: str):
    if not request.url.path.startswith("/dev/"):
        return RedirectResponse(url=f"/?v={video_id}", status_code=303)

    doc = _get_video_doc_for_request(request, video_id)
    if doc is not None:
        doc.update({"likeCount": _firestore_module().Increment(1), "updatedAt": datetime.utcnow().isoformat()})
    return RedirectResponse(url=f"/?v={video_id}", status_code=303)


@app.post("/videos/{video_id}/subscribe")
@app.post("/dev/videos/{video_id}/subscribe")
def subscribe_video(request: Request, video_id: str):
    if not request.url.path.startswith("/dev/"):
        return RedirectResponse(url=f"/?v={video_id}", status_code=303)

    doc = _get_video_doc_for_request(request, video_id)
    if doc is not None:
        doc.update({"subscriberCount": _firestore_module().Increment(1), "updatedAt": datetime.utcnow().isoformat()})
    return RedirectResponse(url=f"/?v={video_id}", status_code=303)


@app.post("/videos/{video_id}/comments")
@app.post("/dev/videos/{video_id}/comments")
def comment_video(request: Request, video_id: str, comment: str = Form(...)):
    if not request.url.path.startswith("/dev/"):
        return RedirectResponse(url=f"/?v={video_id}", status_code=303)

    doc = _get_video_doc_for_request(request, video_id)
    if doc is not None and comment.strip():
        comment_doc = doc.collection("comments").document()
        comment_doc.set(
            {
                "comment": comment.strip(),
                "createdAt": datetime.utcnow().isoformat(),
            }
        )
        doc.update({"commentCount": _firestore_module().Increment(1), "updatedAt": datetime.utcnow().isoformat()})
    return RedirectResponse(url=f"/?v={video_id}", status_code=303)


@app.post("/dev/videos/{video_id}/publish")
def publish_video(request: Request, video_id: str):
    if not request.url.path.startswith("/dev/") or os.environ.get("APP_ENV", "dev").lower() != "dev":
        return RedirectResponse(url=f"/dev/?v={video_id}", status_code=303)

    client = _load_firestore_client()
    if client is None:
        return RedirectResponse(url=f"/dev/?v={video_id}", status_code=303)

    dev_doc = client.collection(_dev_collection_name()).document(video_id)
    prod_doc = client.collection(_prod_collection_name()).document(video_id)
    snapshot = dev_doc.get()
    if snapshot.exists:
        prod_doc.set(snapshot.to_dict())
    return RedirectResponse(url=f"/?v={video_id}", status_code=303)


@app.get("/")
@app.get("/dev/")
def videos_home(request: Request, v: str = "", q: str = ""):
    return render_video_page(request, v, q)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
