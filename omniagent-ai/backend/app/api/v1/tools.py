from fastapi import APIRouter, Depends
from app.deps import current_user
from app.models.user import User
from app.tools.registry import registry

router = APIRouter()


@router.get("/")
def list_tools(_: User = Depends(current_user)):
    return {"tools": registry.names()}


@router.post("/run/{name}")
async def run_tool(name: str, args: dict, user: User = Depends(current_user)):
    args = {**args, "user_id": user.id}
    return {"result": await registry.run(name, args)}