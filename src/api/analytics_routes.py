"""
Search analytics routes.
"""
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.models import SearchLog, User
from src.services.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


class SearchLogResponse(BaseModel):
    id: int
    query: str
    results_count: int
    search_type: Optional[str] = None
    timestamp: datetime


class TrendingQueryResponse(BaseModel):
    query: str
    count: int


class SearchTypeStat(BaseModel):
    search_type: str
    count: int


class SearchStatsResponse(BaseModel):
    total_searches: int
    avg_results: float
    min_results: int
    max_results: int
    search_types: List[SearchTypeStat]


class DailyPatternResponse(BaseModel):
    date: str
    count: int


class PersonalPatternsResponse(BaseModel):
    daily_counts: List[DailyPatternResponse]
    top_queries: List[TrendingQueryResponse]
    avg_results: float
    total_searches: int


def _require_user(current_user: Optional[User]) -> User:
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return current_user


@router.get("/searches", response_model=List[SearchLogResponse])
async def list_search_history(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    user = _require_user(current_user)
    logs = (
        db.query(SearchLog)
        .filter(SearchLog.user_id == user.id)
        .order_by(SearchLog.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return logs


@router.get("/trending", response_model=List[TrendingQueryResponse])
async def get_trending_queries(
    days: int = 7,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    _require_user(current_user)
    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(SearchLog.query, func.count(SearchLog.id).label("count"))
        .filter(SearchLog.timestamp >= since)
        .group_by(SearchLog.query)
        .order_by(func.count(SearchLog.id).desc())
        .limit(limit)
        .all()
    )
    return [{"query": row.query, "count": int(row.count)} for row in rows]


@router.get("/stats", response_model=SearchStatsResponse)
async def get_search_stats(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    user = _require_user(current_user)
    stats = (
        db.query(
            func.count(SearchLog.id),
            func.avg(SearchLog.results_count),
            func.min(SearchLog.results_count),
            func.max(SearchLog.results_count),
        )
        .filter(SearchLog.user_id == user.id)
        .first()
    )

    type_rows = (
        db.query(SearchLog.search_type, func.count(SearchLog.id).label("count"))
        .filter(SearchLog.user_id == user.id)
        .group_by(SearchLog.search_type)
        .all()
    )

    total = int(stats[0] or 0)
    avg_results = float(stats[1] or 0)
    min_results = int(stats[2] or 0)
    max_results = int(stats[3] or 0)
    search_types = [
        {"search_type": row.search_type or "unknown", "count": int(row.count)}
        for row in type_rows
    ]

    return {
        "total_searches": total,
        "avg_results": round(avg_results, 2),
        "min_results": min_results,
        "max_results": max_results,
        "search_types": search_types,
    }


@router.get("/patterns", response_model=PersonalPatternsResponse)
async def get_personal_patterns(
    days: int = 30,
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    user = _require_user(current_user)
    since = datetime.utcnow() - timedelta(days=days)

    daily_rows = (
        db.query(func.date(SearchLog.timestamp).label("date"), func.count(SearchLog.id))
        .filter(SearchLog.user_id == user.id, SearchLog.timestamp >= since)
        .group_by(func.date(SearchLog.timestamp))
        .order_by(func.date(SearchLog.timestamp))
        .all()
    )

    daily_counts = [
        {"date": str(row.date), "count": int(row[1])} for row in daily_rows
    ]

    top_queries = (
        db.query(SearchLog.query, func.count(SearchLog.id).label("count"))
        .filter(SearchLog.user_id == user.id, SearchLog.timestamp >= since)
        .group_by(SearchLog.query)
        .order_by(func.count(SearchLog.id).desc())
        .limit(limit)
        .all()
    )

    avg_results = (
        db.query(func.avg(SearchLog.results_count))
        .filter(SearchLog.user_id == user.id, SearchLog.timestamp >= since)
        .scalar()
    )

    total_searches = (
        db.query(func.count(SearchLog.id))
        .filter(SearchLog.user_id == user.id, SearchLog.timestamp >= since)
        .scalar()
    )

    return {
        "daily_counts": daily_counts,
        "top_queries": [{"query": row.query, "count": int(row.count)} for row in top_queries],
        "avg_results": round(float(avg_results or 0), 2),
        "total_searches": int(total_searches or 0),
    }
