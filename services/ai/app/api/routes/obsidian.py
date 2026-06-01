from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps.auth import require_api_key
from app.obsidian.safety import ObsidianSafetyError
from app.obsidian.vault_service import ObsidianVaultService

router = APIRouter(prefix="/obsidian", tags=["obsidian"], dependencies=[Depends(require_api_key)])


class PathRequest(BaseModel):
    path: str


class SearchRequest(BaseModel):
    query: str
    limit: int = 20


class WriteRequest(BaseModel):
    path: str
    content: str
    overwrite: bool = False


@router.get("/files")
async def list_files(folder: str | None = None) -> dict:
    return _safe(lambda: {"files": ObsidianVaultService().list_files(folder)})


@router.post("/read")
async def read_note(request: PathRequest) -> dict:
    return _safe(lambda: {"path": request.path, "content": ObsidianVaultService().read_note(request.path)})


@router.post("/search")
async def search_notes(request: SearchRequest) -> dict:
    return _safe(lambda: {"matches": ObsidianVaultService().search_notes(request.query, request.limit)})


@router.post("/create")
async def create_note(request: WriteRequest) -> dict:
    return _safe(lambda: ObsidianVaultService().create_note(request.path, request.content, overwrite=request.overwrite))


@router.post("/append")
async def append_note(request: WriteRequest) -> dict:
    return _safe(lambda: ObsidianVaultService().append_note(request.path, request.content))


def _safe(operation):
    try:
        return operation()
    except ObsidianSafetyError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
