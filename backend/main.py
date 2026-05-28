from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.database import init_db
from api.models import router as models_router

app = FastAPI(title="PT-ONNX Benchmark Tool", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(models_router)


@app.on_event("startup")
def startup():
    init_db()
    from services.scan_service import scan_and_register
    from db.database import SessionLocal
    db = SessionLocal()
    try:
        count = scan_and_register(db)
        print(f"Auto-scan: registered {count} new model(s)")
    finally:
        db.close()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "2.0.0"}
