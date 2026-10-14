"""add student consent and timestamps"""
from alembic import op
import sqlalchemy as sa

revision = "0004_student_consent"
down_revision = "0003_topics_materials_required_course"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DELETE FROM quizresponse WHERE student_id IN (SELECT id FROM student WHERE course_id IS NULL)")
    op.execute("DELETE FROM message WHERE student_id IN (SELECT id FROM student WHERE course_id IS NULL)")
    op.execute("DELETE FROM student WHERE course_id IS NULL")
    with op.batch_alter_table("student") as batch:
        batch.add_column(sa.Column("consent_version", sa.String(), nullable=False, server_default="legacy"))
        batch.add_column(sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                                  server_default=sa.text("CURRENT_TIMESTAMP")))
        batch.alter_column("code", existing_type=sa.String(), nullable=True)
        batch.alter_column("course_id", existing_type=sa.Integer(), nullable=False)


def downgrade():
    with op.batch_alter_table("student") as batch:
        batch.drop_column("created_at")
        batch.drop_column("consent_version")
        batch.alter_column("code", existing_type=sa.String(), nullable=False)
        batch.alter_column("course_id", existing_type=sa.Integer(), nullable=True)
