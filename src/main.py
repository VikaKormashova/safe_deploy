from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
import secrets

app = FastAPI()

secret_key = secrets.token_urlsafe(32)
app.add_middleware(SessionMiddleware, secret_key=secret_key)

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

def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

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

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = users_db.get(username)
    if not user or user["password"] != password:
        return HTMLResponse("Login failed", status_code=401)
    request.session["user"] = {"username": user["username"], "role": user["role"]}
    return RedirectResponse(url="/files/my", status_code=303)

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login")

@app.get("/files/my")
def get_my_files(request: Request):
    user = get_current_user(request)
    my_files = [f for f in files_db if f["owner"] == user["username"]]
    return {"files": my_files}

@app.get("/files/{file_id}")
def get_file(request: Request, file_id: int):
    user = get_current_user(request)
    file = next((f for f in files_db if f["id"] == file_id), None)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    if file["owner"] != user["username"] and user["role"] != "admin":
        raise HTTPException(status_code=404, detail="File not found")
    return {"id": file["id"], "filename": file["filename"], "owner": file["owner"], "size": file["size"]}

@app.delete("/files/{file_id}")
def delete_file(request: Request, file_id: int):
    global files_db
    user = get_current_user(request)
    file = next((f for f in files_db if f["id"] == file_id), None)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    if file["owner"] != user["username"] and user["role"] != "admin":
        raise HTTPException(status_code=404, detail="File not found")
    files_db = [f for f in files_db if f["id"] != file_id]
    return {"message": "File deleted"}

@app.get("/")
def root():
    return {"message": "Corporate File Manager API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)