from fastapi import FastAPI
from routers import fraud, chatbot

app = FastAPI(title="Banking AI Service", version="1.0.0")

app.include_router(fraud.router, prefix="/fraud", tags=["Fraud"])
app.include_router(chatbot.router, prefix="/chatbot", tags=["Chatbot"])

@app.get("/")
def root():
    return {"status": "AI service running"}