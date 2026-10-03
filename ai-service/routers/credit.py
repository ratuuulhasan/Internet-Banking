from fastapi import APIRouter
from pydantic import BaseModel
import numpy as np

router = APIRouter()


class CreditFeatures(BaseModel):
    income: float
    existing_loans: int
    tenure_months: int
    interest_rate: float


@router.post("/score")
def score(f: CreditFeatures):
    """
    Simple heuristic credit score (0-100).
    Real project: use trained model.
    """
    score = 50.0
    score += min(f.income / 1000, 30)         # income factor
    score -= f.existing_loans * 5             # existing loans penalty
    score += min(f.tenure_months / 12, 10)    # longer tenure = better
    score -= f.interest_rate / 2              # high rate = risk
    score = max(0, min(100, score))

    decision = "APPROVE" if score >= 60 else "REVIEW" if score >= 40 else "REJECT"

    return {
        "score": round(score, 2),
        "decision": decision,
    }