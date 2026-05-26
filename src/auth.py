from fastapi import HTTPException, Request

users_db = {
    "alice": {"username": "alice", "role": "user", "password": "alice123"},
    "bob": {"username": "bob", "role": "user", "password": "bob123"},
    "admin": {"username": "admin", "role": "admin", "password": "admin123"},
}

files_db = [
    {"id": 1, "filename": "report_alice.pdf", "owner": "alice", "size": 1024},
    {"id": 2, "filename": "photo_bob.jpg", "owner": "bob", "size": 2048},
    {"id": 3, "filename": "admin_keys.txt", "owner": "admin", "size": 512},
]

def get_current_user(request: Request) -> dict:
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

def check_file_permission(file_id: int, user: dict) -> dict:
    file = next((f for f in files_db if f["id"] == file_id), None)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    is_owner = file["owner"] == user["username"]
    is_admin = user["role"] == "admin"
    if not (is_owner or is_admin):
        raise HTTPException(status_code=404, detail="File not found")
    return file

def get_user_files(user: dict) -> list:
    return [f for f in files_db if f["owner"] == user["username"]]