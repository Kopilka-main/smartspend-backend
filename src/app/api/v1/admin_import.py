from fastapi import APIRouter, HTTPException, Request, UploadFile, status

from src.app.core.database import async_session_factory
from src.app.services.xlsx_import import CONFIGS, import_xlsx

router = APIRouter(prefix="/admin/import", tags=["admin-import"])


@router.post("/{entity}")
async def import_entity(entity: str, file: UploadFile, request: Request) -> dict:
    if request.session.get("username") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    if entity not in CONFIGS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown entity: {entity}. Allowed: {', '.join(CONFIGS)}",
        )

    if not file.filename or not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .xlsx files allowed")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    async with async_session_factory() as session:
        result = await import_xlsx(session, entity, data)

    return {
        "created": result.created,
        "updated": result.updated,
        "errors": [{"row": e.row, "message": e.message} for e in result.errors],
    }
