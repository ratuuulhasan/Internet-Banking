from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class Message(BaseModel):
    message: str
    user_email: str = ""

RULES = {
    "balance": "You can view your balance from the Dashboard after login.",
    "transfer": "To transfer money: Go to Transfer → Enter beneficiary → Amount → OTP.",
    "otp": "OTP is sent to your registered phone/email. It expires in 5 minutes.",
    "loan": "Loan application is under Loans menu. AI will check eligibility.",
    "block": "To block your card: Cards → Select card → Block.",
    "kyc": "KYC takes 24-48 hours after submission.",
    "help": "I can help with: balance, transfer, OTP, loan, card, KYC. What do you need?",
}

@router.post("/ask")
def ask(msg: Message):
    text = msg.message.lower()
    for key, reply in RULES.items():
        if key in text:
            return {"reply": reply, "intent": key}
    return {
        "reply": "Sorry, I didn't understand. Try: balance, transfer, OTP, loan, card, KYC.",
        "intent": "unknown"
    }