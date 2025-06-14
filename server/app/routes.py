from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

class StatusMessage(BaseModel):
    id: int
    bid_price: float
    ask_price: float
    timestamp_ns: int
    consumer_id: str

# In-memory store of recent messages
status_store: List[StatusMessage] = []

@router.post("/status")
async def receive_status(msg: StatusMessage):
    print(f"✅ Received from {msg.consumer_id}: {msg}")
    status_store.append(msg)

    # Optional: keep only last 50
    if len(status_store) > 50:
        status_store.pop(0)

    return {"ok": True}

@router.get("/status/latest", response_model=List[StatusMessage])
async def get_latest_status():
    return status_store[-20:]  # Return last 20 for frontend

