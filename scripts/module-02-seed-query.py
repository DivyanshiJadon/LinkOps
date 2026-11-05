from sqlalchemy import delete, select

from app.database import SessionLocal
from app.models import Link


def main():
    with SessionLocal() as session:
        session.execute(
            delete(Link).where(Link.code == "demo123")
        )
        session.commit()

        link = Link(
            code="demo123",
            long_url="https://example.com/bootcamp",
            created_by="local-demo"
        )

        session.add(link)
        session.commit()

        result = session.scalar(
            select(Link).where(Link.code == "demo123")
        )

        print(f"Inserted code: {link.code}")
        print(f"Selected code: {result.code}")
        print(f"Matched long_url: {result.long_url}")


if __name__ == "__main__":
    main()
