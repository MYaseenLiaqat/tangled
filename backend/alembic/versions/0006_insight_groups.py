"""cache insight group titles"""
from alembic import op
import sqlalchemy as sa

revision = "0006_insight_groups"
down_revision = "0005_analysis_quiz"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("analysisjob") as batch:
        batch.add_column(sa.Column("intent", sa.String(), nullable=False, server_default=""))
        batch.add_column(sa.Column("confidence", sa.Float(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("misconception", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column("topic_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_analysisjob_topic_id_concept", "concept", ["topic_id"], ["id"])
        batch.add_column(sa.Column("gap", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column("evidence_phrase", sa.String(), nullable=False, server_default=""))
    op.create_table(
        "insightgroup",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("course.id"), nullable=False),
        sa.Column("concept_id", sa.Integer(), sa.ForeignKey("concept.id"), nullable=False),
        sa.Column("fingerprint", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_insightgroup_course_id", "insightgroup", ["course_id"])
    op.create_index("ix_insightgroup_concept_id", "insightgroup", ["concept_id"])
    op.create_index("ix_insightgroup_fingerprint", "insightgroup", ["fingerprint"])


def downgrade():
    op.drop_table("insightgroup")
    with op.batch_alter_table("analysisjob") as batch:
        batch.drop_column("evidence_phrase")
        batch.drop_column("gap")
        batch.drop_constraint("fk_analysisjob_topic_id_concept", type_="foreignkey")
        batch.drop_column("topic_id")
        batch.drop_column("misconception")
        batch.drop_column("confidence")
        batch.drop_column("intent")
