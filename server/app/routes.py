from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class StatusMessage(BaseModel):
    id: int
    bid_price: float
    ask_price: float
    timestamp_ns: int
    consumer_id: str
    
@router.post("/status")
async def receive_status(msg: StatusMessage):
    print(f"✅ Received from {msg.consumer_id}: {msg}")
    return {"ok": True}
