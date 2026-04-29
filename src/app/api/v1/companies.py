from fastapi import APIRouter, Query

from src.app.core.dependencies import CurrentUser, Session
from src.app.schemas.base import ApiResponse, PaginationMeta
from src.app.schemas.company import BatchCompaniesRequest, CompanyResponse, UserCompanyResponse
from src.app.services.company import CompanyService

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=ApiResponse[list[CompanyResponse]])
async def list_companies(
    session: Session,
    search: str | None = Query(None, alias="q"),
    category_id: str | None = Query(None, alias="categoryId"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    service = CompanyService(session)
    items, total = await service.list_companies(
        search=search,
        category_id=category_id,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(
        data=items,
        meta=PaginationMeta(total=total, limit=limit, offset=offset).model_dump(by_alias=True),
    )


@router.get("/user-companies", response_model=ApiResponse[list[CompanyResponse]])
async def list_user_companies(user: CurrentUser, session: Session):
    service = CompanyService(session)
    return ApiResponse(data=await service.list_user_companies(user.id))


@router.post("/user-companies/batch", response_model=ApiResponse[list[UserCompanyResponse]], status_code=201)
async def sync_user_companies(body: BatchCompaniesRequest, user: CurrentUser, session: Session):
    service = CompanyService(session)
    return ApiResponse(data=await service.sync_user_companies(user.id, body.company_ids))


@router.post("/user-companies/{company_id}", response_model=ApiResponse[UserCompanyResponse], status_code=201)
async def add_user_company(company_id: str, user: CurrentUser, session: Session):
    service = CompanyService(session)
    return ApiResponse(data=await service.add_user_company(user.id, company_id))


@router.delete("/user-companies/{company_id}", response_model=ApiResponse[None])
async def remove_user_company(company_id: str, user: CurrentUser, session: Session):
    service = CompanyService(session)
    await service.remove_user_company(user.id, company_id)
    return ApiResponse(data=None)
