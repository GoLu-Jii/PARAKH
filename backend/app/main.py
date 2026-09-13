"""FastAPI application entrypoint."""
from fastapi import FastAPI

app = FastAPI(title="PARAKH API")

@app.get("/")
def read_root():
    return {"message": "PARAKH API is running"}
