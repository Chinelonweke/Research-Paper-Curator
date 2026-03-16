"""
Collections routes for saved papers.
"""
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from src.database.connection import get_db
from src.database.models import Paper, SavedPaper, User
from src.services.auth import get_current_user

router = APIRouter(prefix="/collections", tags=["collections"])


class SavePaperRequest(BaseModel):
    paper_id: int
    notes: Optional[str] = None


class UpdateNotesRequest(BaseModel):
    notes: str


class PaperResponse(BaseModel):
    id: str
    title: str
    authors: str
    abstract: str
    url: str
    published: Optional[str] = None
    category: Optional[str] = None


class SavedPaperResponse(BaseModel):
    id: int
    user_id: int
    paper_id: int
    saved_at: str
    notes: Optional[str] = None
    paper: Optional[PaperResponse] = None


def _require_user(current_user: Optional[User]) -> User:
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return current_user


def _serialize_paper(paper: Paper) -> PaperResponse:
    return PaperResponse(
        id=str(paper.id),
        title=paper.title,
        authors=paper.authors,
        abstract=paper.abstract,
        url=paper.pdf_url or "",
        published=paper.published_date.strftime("%Y-%m-%d") if paper.published_date else None,
        category=paper.primary_category or "Unknown",
    )


def _serialize_saved_paper(saved: SavedPaper) -> SavedPaperResponse:
    return SavedPaperResponse(
        id=saved.id,
        user_id=saved.user_id,
        paper_id=saved.paper_id,
        saved_at=saved.saved_at.isoformat(),
        notes=saved.notes,
        paper=_serialize_paper(saved.paper) if saved.paper else None,
    )


@router.get("/saved", response_model=List[SavedPaperResponse])
async def list_saved_papers(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    user = _require_user(current_user)
    saved_papers = (
        db.query(SavedPaper)
        .options(joinedload(SavedPaper.paper))
        .filter(SavedPaper.user_id == user.id)
        .order_by(SavedPaper.saved_at.desc())
        .all()
    )
    return [_serialize_saved_paper(saved) for saved in saved_papers]


@router.post("/save", response_model=SavedPaperResponse)
async def save_paper(
    request: SavePaperRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    user = _require_user(current_user)
    paper = db.query(Paper).filter(Paper.id == request.paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    existing = (
        db.query(SavedPaper)
        .filter(SavedPaper.user_id == user.id, SavedPaper.paper_id == request.paper_id)
        .options(joinedload(SavedPaper.paper))
        .first()
    )
    if existing:
        if request.notes is not None:
            existing.notes = request.notes
            db.commit()
            db.refresh(existing)
        return _serialize_saved_paper(existing)

    saved = SavedPaper(user_id=user.id, paper_id=request.paper_id, notes=request.notes)
    db.add(saved)
    db.commit()
    db.refresh(saved)
    saved.paper = paper
    return _serialize_saved_paper(saved)


@router.delete("/{saved_paper_id}")
async def delete_saved_paper(
    saved_paper_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    user = _require_user(current_user)
    saved = (
        db.query(SavedPaper)
        .filter(SavedPaper.id == saved_paper_id, SavedPaper.user_id == user.id)
        .first()
    )
    if not saved:
        raise HTTPException(status_code=404, detail="Saved paper not found")

    db.delete(saved)
    db.commit()
    return {"success": True}


@router.put("/{saved_paper_id}/notes", response_model=SavedPaperResponse)
async def update_saved_paper_notes(
    saved_paper_id: int,
    request: UpdateNotesRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    user = _require_user(current_user)
    saved = (
        db.query(SavedPaper)
        .options(joinedload(SavedPaper.paper))
        .filter(SavedPaper.id == saved_paper_id, SavedPaper.user_id == user.id)
        .first()
    )
    if not saved:
        raise HTTPException(status_code=404, detail="Saved paper not found")

    saved.notes = request.notes
    db.commit()
    db.refresh(saved)
    return _serialize_saved_paper(saved)