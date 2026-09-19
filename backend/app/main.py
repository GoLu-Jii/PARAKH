"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers.onboarding import router as onboarding_router
from app.routers.topics import router as topics_router

app = FastAPI(title="PARAKH API", version="1.0.0")

# CORS setup
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]
if settings.cors_origins:
    origins.extend([o.strip() for o in settings.cors_origins.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(onboarding_router)
app.include_router(topics_router)


@app.get("/")
def read_root():
    return {"message": "PARAKH API is running", "status": "healthy"}
