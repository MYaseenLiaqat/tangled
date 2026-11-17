"""persist student answer citations"""
from alembic import op
import sqlalchemy as sa

revision = "0007_message_sources"
down_revision = "0006_insight_groups"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("message") as batch:
        batch.add_column(sa.Column("sources_json", sa.String(), nullable=False, server_default="[]"))


def downgrade():
    with op.batch_alter_table("message") as batch:
        batch.drop_column("sources_json")
