from typing import List

from fastapi import APIRouter

from ..database.DAO import dao
from ..models.TaskCollections.TaskCollection import TaskCollectionCreationRequestObject

router = APIRouter()


@router.get("/fetchTaskCollection")
async def fetch_task_collection(id: int) -> List[int]:
    return dao.fetch_task_collection(id)


@router.post("/createTaskCollection")
async def create_task_collection_route(
    request: TaskCollectionCreationRequestObject,
) -> int:
    id = dao.store_task_collection(
        request.task_collection, request.task_collection_name
    )
    return id
