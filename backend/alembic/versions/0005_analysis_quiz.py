"""add analysis jobs and aggregate quiz data"""
from alembic import op
import sqlalchemy as sa

revision = "0005_analysis_quiz"
down_revision = "0004_student_consent"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "analysisjob",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("message_id", sa.Integer(), sa.ForeignKey("message.id"), nullable=False),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("course.id"), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.String(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_analysisjob_message_id", "analysisjob", ["message_id"], unique=True)
    op.create_index("ix_analysisjob_course_id", "analysisjob", ["course_id"])
    op.create_table(
        "quizaggregate",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("course.id"), nullable=False),
        sa.Column("item", sa.String(), nullable=False),
        sa.Column("concept_id", sa.Integer(), sa.ForeignKey("concept.id")),
        sa.Column("concept_name", sa.String(), nullable=False),
        sa.Column("option", sa.String(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("correct", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_quizaggregate_course_id", "quizaggregate", ["course_id"])
    op.create_index("ix_quizaggregate_item", "quizaggregate", ["item"])


def downgrade():
    op.drop_table("quizaggregate")
    op.drop_table("analysisjob")
