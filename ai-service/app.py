from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import fraud, chatbot, credit

app = FastAPI(
    title="Banking AI Service",
    description="Fraud Detection + Chatbot + Credit Scoring",
    version="2.0.0",
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
    return {
        "status": "ok",
        "fraud_model_loaded": MODEL is not None,
    }