from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routers import fraud, chatbot, credit


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: warm up models
    print("🚀 AI service starting...")
    
    # 1. Load fraud model registry
    try:
        from services.model_registry import registry
        registry.load()
        print(f"✅ Fraud model loaded: {registry.version_tag}")
    except Exception as e:
        print(f"⚠️  Fraud model load failed: {e}")
    
    # 2. Build FAISS index (chatbot)
    try:
        from chatbot.vector_store import vector_store
        vector_store.build(force=False)   # Load if exists, build if not
        print(f"✅ FAISS loaded: {len(vector_store.chunks)} chunks")
    except Exception as e:
        print(f"⚠️  FAISS load failed: {e}")
    
    # 3. Warm up embeddings (LaBSE)
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
    description="Fraud Detection + Chatbot + Credit Scoring",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fraud.router, prefix="/fraud", tags=["Fraud Detection"])
app.include_router(chatbot.router, prefix="/chatbot", tags=["Chatbot"])
app.include_router(credit.router, prefix="/credit", tags=["Credit Scoring"])


@app.get("/")
def root():
    return {"status": "AI service running", "version": "2.0.0"}


@app.get("/health")
def health():
    from routers.fraud import MODEL
    from chatbot.vector_store import vector_store
    return {
        "status": "ok",
        "fraud_model_loaded": MODEL is not None,
        "chatbot_index_loaded": vector_store.index is not None,
        "chatbot_chunks": len(vector_store.chunks),
    }