from fastapi import FastAPI, Request, Form, HTTPException, Depends, UploadFile, File, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
import secrets
import uuid
import os
import filetype
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

from src.auth import (
    users_db, files_db, get_current_user, check_file_permission,
    get_user_files, save_file_metadata, STORAGE_DIR
)

app = FastAPI(title="Corporate File Manager")

secret_key = secrets.token_urlsafe(32)
app.add_middleware(SessionMiddleware, secret_key=secret_key)

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise RuntimeError("ENCRYPTION_KEY not set in .env file")
cipher = Fernet(ENCRYPTION_KEY.encode())

MAX_FILE_SIZE = 2 * 1024 * 1024
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png"]

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = users_db.get(username)
    if not user or user["password"] != password:
        return HTMLResponse("Login failed", status_code=401)
    request.session["user"] = {"username": user["username"], "role": user["role"]}
    return RedirectResponse(url="/files/my", status_code=303)

@app.get("/login")
def login_form():
    return HTMLResponse('''
    <html>
    <body>
        <h1>Login</h1>
        <form method="post">
            <input type="text" name="username" placeholder="Username"><br>
            <input type="password" name="password" placeholder="Password"><br>
            <button type="submit">Login</button>
        </form>
        <p>alice/alice123, bob/bob123, admin/admin123</p>
    </body>
    </html>
    ''')

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login")

@app.get("/files/my")
def get_my_files(request: Request):
    user = get_current_user(request)
    return {"files": get_user_files(user)}

@app.get("/files/{file_id}")
def get_file(request: Request, file_id: int):
    user = get_current_user(request)
    file = check_file_permission(file_id, user)
    return {"id": file["id"], "filename": file["filename"], "owner": file["owner"], "size": file["size"], "is_encrypted": file.get("is_encrypted", False)}

@app.delete("/files/{file_id}")
def delete_file(request: Request, file_id: int):
    global files_db
    user = get_current_user(request)
    file = check_file_permission(file_id, user)
    if file.get("path") and os.path.exists(file["path"]):
        os.remove(file["path"])
    files_db = [f for f in files_db if f["id"] != file_id]
    return {"message": "File deleted"}

@app.post("/files/upload")
async def upload_file(request: Request, file: UploadFile = File(...), encrypt: bool = Query(False)):
    user = get_current_user(request)
    size = 0

    kind = filetype.guess(await file.read(2048))
    await file.seek(0)
    if kind is None or kind.mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed: {ALLOWED_MIME_TYPES}")

    data = await file.read()
    size = len(data)

    if size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Max 2MB")

    if encrypt:
        data_to_save = cipher.encrypt(data)
    else:
        data_to_save = data

    os.makedirs(STORAGE_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1]
    physical_name = f"{uuid.uuid4().hex}{ext}"
    physical_path = os.path.join(STORAGE_DIR, physical_name)

    try:
        with open(physical_path, "wb") as buffer:
            buffer.write(data_to_save)
    except Exception as e:
        if os.path.exists(physical_path):
            os.remove(physical_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    file_metadata = save_file_metadata(file.filename, user["username"], size, physical_path, is_encrypted=encrypt)
    return {"message": "File uploaded", "file_id": file_metadata["id"], "original_name": file_metadata["filename"], "encrypted": encrypt}

@app.get("/files/{file_id}/download")
def download_file(request: Request, file_id: int):
    user = get_current_user(request)
    file_metadata = check_file_permission(file_id, user)

    if not file_metadata.get("path") or not os.path.exists(file_metadata["path"]):
        raise HTTPException(status_code=404, detail="File not found on server")

    with open(file_metadata["path"], "rb") as f:
        file_data = f.read()

    if file_metadata.get("is_encrypted", False):
        try:
            file_data = cipher.decrypt(file_data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Decryption failed: {str(e)}")

    from fastapi.responses import Response
    from urllib.parse import quote

    encoded_filename = quote(file_metadata["filename"])
    return Response(
        content=file_data,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )

@app.get("/upload-form")
def upload_form(request: Request):
    user = get_current_user(request)
    return HTMLResponse('''
    <html>
    <body>
        <h1>Загрузка файла</h1>
        <form action="/files/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept="image/jpeg,image/png" required><br>
            <input type="checkbox" name="encrypt" value="true"> Зашифровать файл<br>
            <button type="submit">Загрузить</button>
        </form>
        <p><a href="/files/my">Мои файлы</a></p>
        <p><a href="/logout">Выйти</a></p>
    </body>
    </html>
    ''')

@app.get("/")
def root():
    return {"message": "Corporate File Manager API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)