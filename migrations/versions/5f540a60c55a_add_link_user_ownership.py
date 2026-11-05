"""add link user ownership"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "5f540a60c55a"
down_revision: Union[str, Sequence[str], None] = "b4d0310f30fc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    if bind.execute(sa.text("SELECT id FROM users WHERE id = 1")).first() is None:
        raise RuntimeError("User ID 1 does not exist. Migration stopped.")

    op.drop_index("ix_links_created_by", table_name="links")

    op.add_column(
        "links",
        sa.Column("created_by_new", sa.Integer(), nullable=True),
    )

    op.execute("UPDATE links SET created_by_new = 1")

    op.drop_column("links", "created_by")

    op.alter_column(
        "links",
        "created_by_new",
        new_column_name="created_by",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.create_foreign_key(
        "fk_links_created_by_users",
        "links",
        "users",
        ["created_by"],
        ["id"],
    )

    op.create_index(
        "ix_links_created_by",
        "links",
        ["created_by"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_links_created_by", table_name="links")

    op.drop_constraint(
        "fk_links_created_by_users",
        "links",
        type_="foreignkey",
    )

    op.add_column(
        "links",
        sa.Column("created_by_old", sa.String(length=100), nullable=True),
    )

    op.execute("UPDATE links SET created_by_old = 'local-demo'")

    op.drop_column("links", "created_by")

    op.alter_column(
        "links",
        "created_by_old",
        new_column_name="created_by",
        existing_type=sa.String(length=100),
        nullable=False,
    )

    op.create_index(
        "ix_links_created_by",
        "links",
        ["created_by"],
        unique=False,
    )
