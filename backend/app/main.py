from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from app import seed
from app.routers import api

app = FastAPI(title="闸对", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_STATIC = Path(__file__).resolve().parent / "static"


@app.on_event("startup")
def _启动():
    seed.初始化库()


app.include_router(api)


@app.get("/login", response_class=HTMLResponse)
def 登录页():
    p = _STATIC / "login.html"
    if p.is_file():
        return HTMLResponse(p.read_text(encoding="utf-8"))
    return HTMLResponse(
        "<html><body><h1>登录</h1>"
        '<form><label>账号<input name="user"/></label>'
        '<label>密码<input type="password" name="password"/></label>'
        "<button>登录</button></form></body></html>"
    )


if _STATIC.is_dir():
    app.mount("/", StaticFiles(directory=str(_STATIC), html=True), name="static")
