import os
from uuid import uuid4
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
UPLOAD_FOLDER = "uploads"


def ensure_upload_folder():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_image(file_storage):
    ensure_upload_folder()

    if not file_storage or not file_storage.filename:
        return None, "Aucun fichier reçu"

    if not allowed_file(file_storage.filename):
        return None, "Format non supporté"

    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid4().hex}.{ext}"
    safe_name = secure_filename(filename)
    full_path = os.path.join(UPLOAD_FOLDER, safe_name)

    file_storage.save(full_path)

    return {
        "filename": safe_name,
        "path": full_path,
        "url": f"/uploads/{safe_name}"
    }, None