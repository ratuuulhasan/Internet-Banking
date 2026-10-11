from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routers import fraud, chatbot, credit, ocr


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 AI service starting...")

    # 1. Fraud model
    try:
        from services.model_registry import registry
        registry.load()
        print(f"✅ Fraud model loaded: {registry.version_tag}")
    except Exception as e:
        print(f"⚠️  Fraud model load failed: {e}")

    # 2. FAISS index (chatbot)
    try:
        from chatbot.vector_store import vector_store
        vector_store.build(force=False)
        print(f"✅ FAISS loaded: {len(vector_store.chunks)} chunks")
    except Exception as e:
        print(f"⚠️  FAISS load failed: {e}")

    # 3. LaBSE embeddings
    try:
        from chatbot.embeddings import embeddings
        embeddings.load()
        print("✅ LaBSE embeddings warmed up")
    except Exception as e:
        print(f"⚠️  Embeddings load failed: {e}")

    print("✅ AI service ready")
    yield
    print("🛑 AI service shutting down")


app = FastAPI(
    title="Banking AI Service",
    description="Fraud Detection + Chatbot + Credit Scoring + NID OCR",
    version="2.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Routers ----
app.include_router(fraud.router,    prefix="/fraud",    tags=["Fraud Detection"])
app.include_router(chatbot.router,  prefix="/chatbot",  tags=["Chatbot"])
app.include_router(credit.router,   prefix="/credit",   tags=["Credit Scoring"])
app.include_router(ocr.router,      prefix="/ocr",      tags=["NID OCR"])


@app.get("/")
def root():
    return {"status": "AI service running", "version": "2.1.0"}


@app.get("/health")
def health():
    """
    Full health check for all AI service components.
    """
    # Fraud model — via registry
    try:
        from services.model_registry import registry
        registry.check_reload()
        if not registry.is_loaded:
            registry.load()
        fraud_loaded = registry.model is not None
        fraud_version = registry.version_tag
    except Exception as e:
        fraud_loaded = False
        fraud_version = f"error: {e}"

    # Chatbot
    try:
        from chatbot.vector_store import vector_store
        chatbot_loaded = vector_store.index is not None
        chatbot_chunks = len(vector_store.chunks)
    except Exception:
        chatbot_loaded = False
        chatbot_chunks = 0

    # OCR
    try:
        from ocr.nid_extractor import _reader
        ocr_loaded = _reader is not None
    except Exception:
        ocr_loaded = False

    # Face recognition
    try:
        from ocr.face_matcher import FACE_RECOGNITION_AVAILABLE
        face_rec = FACE_RECOGNITION_AVAILABLE
    except Exception:
        face_rec = False

    return {
        "status": "ok",
        "fraud_model_loaded": fraud_loaded,
        "fraud_model_version": fraud_version,
        "chatbot_index_loaded": chatbot_loaded,
        "chatbot_chunks": chatbot_chunks,
        "ocr_loaded": ocr_loaded,
        "face_recognition": face_rec,
    }