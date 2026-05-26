from fastapi import FastAPI
from src.schemas import UserCreate

app = FastAPI(title="Corporate File Manager", description="API для регистрации пользователей")


@app.post("/registration")
def register(user: UserCreate):
    """Регистрация нового пользователя"""
    return {"msg": "User created", "user": user.username}