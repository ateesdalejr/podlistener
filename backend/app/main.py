from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import feeds, episodes, keywords, mentions, dashboard


def create_app() -> FastAPI:
    app = FastAPI(title="PodListener", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(feeds.router, prefix="/api/v1")
    app.include_router(episodes.router, prefix="/api/v1")
    app.include_router(keywords.router, prefix="/api/v1")
    app.include_router(mentions.router, prefix="/api/v1")
    app.include_router(dashboard.router, prefix="/api/v1")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
