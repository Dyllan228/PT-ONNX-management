from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.database import init_db

app = FastAPI(title="PT-ONNX Benchmark Tool", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "2.0.0"}
