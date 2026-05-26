from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from jinja2 import Template
import bleach

app = FastAPI()
templates = Jinja2Templates(directory="templates")

comments_db = []

def sanitize_text(text: str) -> str:
    allowed_tags = ['b', 'i', 'u', 'em', 'strong']
    return bleach.clean(text, tags=allowed_tags, strip=True)

# ===== CSP MIDDLEWARE (ДОБАВЛЯЕМ ЗАГОЛОВКИ) =====
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response

@app.get("/comments")
def show_comments(request: Request):
    return templates.TemplateResponse("comments.html", {
        "request": request,
        "comments": comments_db
    })

@app.post("/comments")
def add_comment(comment_text: str = Form(...)):
    safe_comment = sanitize_text(comment_text)
    comments_db.append(safe_comment)
    return RedirectResponse(url="/comments", status_code=303)

@app.get("/vulnerable/comments")
def vulnerable_comments(request: Request):
    html = """
    <html>
    <body>
        <h1>⚠️ УЯЗВИМАЯ СТРАНИЦА ⚠️</h1>
        <form method="POST" action="/vulnerable/comments">
            <textarea name="comment_text" rows="4" cols="50"></textarea><br>
            <button type="submit">Отправить</button>
        </form>
        <h2>Комментарии:</h2>
        {% for c in comments %}
            <div>{{ c|safe }}</div>
        {% endfor %}
        <p><a href="/comments">Перейти на защищённую страницу</a></p>
    </body>
    </html>
    """
    return HTMLResponse(content=Template(html).render(comments=comments_db))

@app.post("/vulnerable/comments")
def vulnerable_add_comment(comment_text: str = Form(...)):
    comments_db.append(comment_text)
    return RedirectResponse(url="/vulnerable/comments", status_code=303)

@app.get("/")
def root():
    return {"message": "API работает", "endpoints": ["/comments", "/vulnerable/comments"]}
