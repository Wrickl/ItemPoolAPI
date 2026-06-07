from fastapi import APIRouter

from models.Enums.License import License
from models.Enums.Questionstypes import Questiontypes

router = APIRouter()


@router.get("/getAllAvailableQuestionTypes")
async def get_available_question_types():
    return [k.value for k in Questiontypes]


@router.get("/getAllAvailableLicenseTypes")
async def get_available_license_types():
    return [k.value for k in License]
