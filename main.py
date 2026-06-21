"""Nikhil Funtime — FastAPI app for archive-backed videos."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from typing import Any

from datetime import datetime

from fastapi import Cookie, HTTPException, Response
from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = os.path.dirname(__file__)
DEFAULT_FIRESTORE_COLLECTION = "videos"
DEFAULT_FIRESTORE_DEV_COLLECTION = "dev_videos"
DEFAULT_FIRESTORE_DATABASE = "default"
DEFAULT_USERS_COLLECTION = "users"
DEFAULT_ACTIONS_COLLECTION = "video_actions"
SESSION_COOKIE_NAME = "nf_session"
SESSION_SIGNING_SECRET = os.environ.get("SESSION_SIGNING_SECRET", "dev-session-secret").encode("utf-8")
BASE_PATH = os.environ.get("BASE_PATH", "").rstrip("/")
STATIC_PATH = f"{BASE_PATH}/static" if BASE_PATH else "/static"
HOME_PATH = f"{BASE_PATH}/" if BASE_PATH else "/"
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "88pawankumarjha@gmail.com").lower()

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


def _firebase_admin_auth():
    import firebase_admin
    from firebase_admin import auth, credentials

    if not firebase_admin._apps:
        credentials_path = _credentials_path()
        if not credentials_path or not os.path.exists(credentials_path):
            raise RuntimeError("Missing Firebase service account JSON")
        firebase_admin.initialize_app(credentials.Certificate(credentials_path))
    return auth


def _encode_session_payload(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    body = base64.urlsafe_b64encode(raw).decode("ascii")
    sig = hmac.new(SESSION_SIGNING_SECRET, body.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def _decode_session_payload(session_value: str | None) -> dict[str, Any] | None:
    if not session_value or "." not in session_value:
        return None
    body, sig = session_value.rsplit(".", 1)
    expected = hmac.new(SESSION_SIGNING_SECRET, body.encode("ascii"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        raw = base64.urlsafe_b64decode(body.encode("ascii"))
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


def _current_user(request: Request) -> dict[str, Any] | None:
    return _decode_session_payload(request.cookies.get(SESSION_COOKIE_NAME))


def _is_admin_user(user: dict[str, Any] | None) -> bool:
    return bool(user and str(user.get("email", "")).lower() == ADMIN_EMAIL)


def _user_doc_id(user_id: str) -> str:
    return user_id.replace("/", "_")


def _upsert_user_profile(user: dict[str, Any], provider: str = "google") -> None:
    client = _load_firestore_client()
    if client is None:
        return
    user_id = user.get("uid") or user.get("sub") or user.get("email")
    if not user_id:
        return
    client.collection(DEFAULT_USERS_COLLECTION).document(_user_doc_id(user_id)).set(
        {
            "uid": user_id,
            "email": user.get("email"),
            "name": user.get("name") or user.get("displayName"),
            "photoURL": user.get("picture") or user.get("photoURL"),
            "provider": provider,
            "isAdmin": _is_admin_user(user),
            "lastLoginAt": datetime.utcnow().isoformat(),
        },
        merge=True,
    )


def _record_action(video_id: str, action_type: str, user: dict[str, Any] | None, comment: str | None = None) -> None:
    client = _load_firestore_client()
    if client is None:
        return
    payload = {
        "videoId": video_id,
        "actionType": action_type,
        "userId": user.get("uid") if user else None,
        "userEmail": user.get("email") if user else None,
        "userName": user.get("name") if user else None,
        "createdAt": datetime.utcnow().isoformat(),
    }
    if comment:
        payload["comment"] = comment
    client.collection(DEFAULT_ACTIONS_COLLECTION).document().set(payload)


def _session_response(user: dict[str, Any], redirect_to: str) -> RedirectResponse:
    response = RedirectResponse(url=redirect_to, status_code=303)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        _encode_session_payload(user),
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
        path="/",
    )
    return response


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


def _firebase_web_config() -> dict[str, str]:
    return {
        "apiKey": os.environ.get("FIREBASE_WEB_API_KEY", ""),
        "authDomain": os.environ.get("FIREBASE_WEB_AUTH_DOMAIN", ""),
        "projectId": os.environ.get("FIREBASE_WEB_PROJECT_ID", ""),
        "appId": os.environ.get("FIREBASE_WEB_APP_ID", ""),
        "messagingSenderId": os.environ.get("FIREBASE_WEB_MESSAGING_SENDER_ID", ""),
        "storageBucket": os.environ.get("FIREBASE_WEB_STORAGE_BUCKET", ""),
    }


def render_video_page(request: Request, v: str = "", q: str = ""):
    all_videos, firestore_ready = load_videos_from_firestore(request)
    path_context = _paths_for_request(request)
    current_user = _current_user(request)
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
                "current_user": current_user,
                "is_admin": _is_admin_user(current_user),
                "firebase_web_config": _firebase_web_config(),
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
            "current_user": current_user,
            "is_admin": _is_admin_user(current_user),
            "firebase_web_config": _firebase_web_config(),
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

    user = _current_user(request)
    if not user:
        return RedirectResponse(url=f"/dev/?v={video_id}", status_code=303)
    doc = _get_video_doc_for_request(request, video_id)
    if doc is not None:
        doc.update({"likeCount": _firestore_module().Increment(1), "updatedAt": datetime.utcnow().isoformat()})
        _record_action(video_id, "like", user)
    return RedirectResponse(url=f"/?v={video_id}", status_code=303)


@app.post("/videos/{video_id}/subscribe")
@app.post("/dev/videos/{video_id}/subscribe")
def subscribe_video(request: Request, video_id: str):
    if not request.url.path.startswith("/dev/"):
        return RedirectResponse(url=f"/?v={video_id}", status_code=303)

    user = _current_user(request)
    if not user:
        return RedirectResponse(url=f"/dev/?v={video_id}", status_code=303)
    doc = _get_video_doc_for_request(request, video_id)
    if doc is not None:
        doc.update({"subscriberCount": _firestore_module().Increment(1), "updatedAt": datetime.utcnow().isoformat()})
        _record_action(video_id, "subscribe", user)
    return RedirectResponse(url=f"/?v={video_id}", status_code=303)


@app.post("/videos/{video_id}/comments")
@app.post("/dev/videos/{video_id}/comments")
def comment_video(request: Request, video_id: str, comment: str = Form(...)):
    if not request.url.path.startswith("/dev/"):
        return RedirectResponse(url=f"/?v={video_id}", status_code=303)

    user = _current_user(request)
    if not user:
        return RedirectResponse(url=f"/dev/?v={video_id}", status_code=303)
    doc = _get_video_doc_for_request(request, video_id)
    if doc is not None and comment.strip():
        comment_doc = doc.collection("comments").document()
        comment_doc.set(
            {
                "comment": comment.strip(),
                "createdAt": datetime.utcnow().isoformat(),
                "userEmail": user.get("email") if user else None,
                "userName": user.get("name") if user else None,
            }
        )
        doc.update({"commentCount": _firestore_module().Increment(1), "updatedAt": datetime.utcnow().isoformat()})
        _record_action(video_id, "comment", user, comment.strip())
    return RedirectResponse(url=f"/?v={video_id}", status_code=303)


@app.post("/dev/videos/{video_id}/publish")
def publish_video(request: Request, video_id: str):
    user = _current_user(request)
    if not request.url.path.startswith("/dev/") or os.environ.get("APP_ENV", "dev").lower() != "dev" or not _is_admin_user(user):
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


@app.post("/auth/google")
def auth_google(request: Request, id_token: str = Form(...), redirect_to: str = Form("/")):
    try:
        auth = _firebase_admin_auth()
        decoded = auth.verify_id_token(id_token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid Google sign-in") from exc

    user = {
        "uid": decoded.get("uid"),
        "email": decoded.get("email"),
        "name": decoded.get("name") or decoded.get("displayName"),
        "picture": decoded.get("picture"),
        "provider": "google",
    }
    _upsert_user_profile(user)
    return _session_response(user, redirect_to or "/")


@app.post("/auth/logout")
def auth_logout(redirect_to: str = Form("/")):
    response = RedirectResponse(url=redirect_to or "/", status_code=303)
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return response


@app.get("/")
@app.get("/dev/")
def videos_home(request: Request, v: str = "", q: str = ""):
    return render_video_page(request, v, q)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
