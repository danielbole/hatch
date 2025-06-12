from fastapi import APIRouter, HTTPException


router = APIRouter(
    prefix="/test",
    tags=["test"]
)

request_count = 0

@router.post("/messages/receive")
async def test_receive_message(json: dict):
    # global request_count
    # request_count += 1
    # if request_count < 4:
    #     raise HTTPException(status_code=429, detail=f"Too many requests, please try again later. {request_count}")
    return {"status": "success", "message": "Message received successfully", "data": json}