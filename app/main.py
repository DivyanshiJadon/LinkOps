import json
from app.cache import redis_client
import secrets

from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.database import get_db
from app.models import Link, ClickEvent
from app.schemas import LinkCreate, LinkResponse

app = FastAPI()


@app.get("/health")
def health_check():
    return {"ok": True}


@app.post("/links", response_model=LinkResponse)
def create_link(
    link_data: LinkCreate,
    db: Session = Depends(get_db)
):

    code = link_data.custom_code or secrets.token_urlsafe(6)

    existing_link = db.query(Link).filter(Link.code == code).first()

    if existing_link:
        raise HTTPException(
            status_code=409,
            detail="This short code is already taken"
        )
    new_link = Link(
        code=code,
        long_url=str(link_data.long_url),
        expires_at=link_data.expires_at,
        tags=link_data.tags,
        created_by="local-demo"
    )

    db.add(new_link)
    db.commit()
    db.refresh(new_link)

    return {
        "id": new_link.id,
        "code": new_link.code,
        "short_url": f"/r/{new_link.code}",
        "long_url": new_link.long_url,
        "created_at": new_link.created_at
    }


@app.get("/links", response_model=list[LinkResponse])
def list_links(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    links = (
        db.query(Link)
        .order_by(Link.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": link.id,
            "code": link.code,
            "short_url": f"/r/{link.code}",
            "long_url": link.long_url,
            "created_at": link.created_at
        }
        for link in links
    ]


@app.get("/links/{link_id}", response_model=LinkResponse)
def get_link(
    link_id: int,
    db: Session = Depends(get_db)
):
    link = db.query(Link).filter(Link.id == link_id).first()

    if not link:
        raise HTTPException(
            status_code=404,
            detail="Link not found"
        )

    return {
        "id": link.id,
        "code": link.code,
        "short_url": f"/r/{link.code}",
        "long_url": link.long_url,
        "created_at": link.created_at
    }
@app.put("/links/{link_id}")
def update_link(
    link_id: int,
    link_data: LinkCreate,
    db: Session = Depends(get_db)
):
    link = db.query(Link).filter(Link.id == link_id).first()

    if not link:
        raise HTTPException(
            status_code=404,
            detail="Link not found"
        )

    old_code = link.code

    link.long_url = str(link_data.long_url)
    link.expires_at = link_data.expires_at
    link.tags = link_data.tags

    db.commit()
    db.refresh(link)

    # Remove the old cached link from Redis
    redis_client.delete(f"link:{old_code}")

    return {
        "message": "Link updated successfully",
        "id": link.id,
        "code": link.code,
        "short_url": f"/r/{link.code}",
        "long_url": link.long_url
    }

@app.delete("/links/{link_id}")
def delete_link(
    link_id: int,
    db: Session = Depends(get_db)
):
    link = db.query(Link).filter(Link.id == link_id).first()

    if not link:
        raise HTTPException(
            status_code=404,
            detail="Link not found"
        )

    # Delete associated click history first
    db.query(ClickEvent).filter(
        ClickEvent.link_id == link_id
    ).delete(synchronize_session=False)

    # Remove the Redis cache entry
    redis_client.delete(f"link:{link.code}")

    # Delete the link
    db.delete(link)
    db.commit()

    return {
        "message": "Link deleted successfully",
        "id": link_id
    }



@app.get("/r/{code}")
def redirect_link(
    code: str,
    request: Request,
    db: Session = Depends(get_db)
):
    cache_key = f"link:{code}"
    cached_link = redis_client.get(cache_key)

    if cached_link:
        link_data = json.loads(cached_link)
        link_id = link_data["id"]
        long_url = link_data["long_url"]
        expires_at = (
            datetime.fromisoformat(link_data["expires_at"])
            if link_data["expires_at"]
            else None
        )
    else:
        link = db.query(Link).filter(Link.code == code).first()

        if not link:
            raise HTTPException(
                status_code=404,
                detail="Short link not found"
            )

        link_id = link.id
        long_url = link.long_url
        expires_at = link.expires_at

        if not expires_at or expires_at > datetime.now(timezone.utc):
            redis_client.setex(
                cache_key,
                300,
                json.dumps({
                    "id": link_id,
                    "long_url": long_url,
                    "expires_at": expires_at.isoformat() if expires_at else None
                })
            )

    if expires_at and expires_at <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=410,
            detail="Short link has expired"
        )

    click_event = ClickEvent(
        link_id=link_id,
        user_agent=request.headers.get("user-agent"),
        referrer=request.headers.get("referer"),
        ip_hash=None
    )

    db.add(click_event)
    db.commit()

    return RedirectResponse(
        url=long_url,
        status_code=307
    )


@app.get("/links/{link_id}/analytics")
def get_link_analytics(
    link_id: int,
    db: Session = Depends(get_db)
):
    link = db.query(Link).filter(Link.id == link_id).first()

    if not link:
        raise HTTPException(
            status_code=404,
            detail="Link not found"
        )

    total_clicks = (
        db.query(ClickEvent)
        .filter(ClickEvent.link_id == link_id)
        .count()
    )

    return {
        "link_id": link.id,
        "short_code": link.code,
        "total_clicks": total_clicks
    }
