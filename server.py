from typing import List

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware

from api import router


def init_routers(app: FastAPI) -> None:
    app.include_router(router, prefix="/api")

def make_middleware() -> List[Middleware]:
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
    ]
    return middleware

def create_app() -> FastAPI:
    app_ = FastAPI(title="Lexsy Backend", middleware=make_middleware())
    init_routers(app_)
    return app_

app = create_app()
