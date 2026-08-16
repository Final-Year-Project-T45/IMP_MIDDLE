from fastapi import APIRouter, Query
from app.services.policy_service import policy_kb

router = APIRouter(prefix="/api/policies", tags=["Policies"])

@router.get("")
def list_policies():
    return policy_kb.list_all_policies()

@router.get("/search")
def search_policies(q: str = Query(..., description="Semantic policy search query")):
    return policy_kb.search(q, top_k=3)
