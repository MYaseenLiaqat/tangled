"""require course ownership for topics and materials"""
from alembic import op
import sqlalchemy as sa

revision = "0003_topics_materials_required_course"
down_revision = "0002_instructors_courses"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DELETE FROM verdict")
    op.execute("DELETE FROM quizresponse")
    op.execute("DELETE FROM quizitem")
    op.execute("DELETE FROM message")
    op.execute("DELETE FROM material")
    op.execute("DELETE FROM concept")
    with op.batch_alter_table("material") as batch:
        batch.add_column(sa.Column("error", sa.String(), nullable=False, server_default=""))
        batch.alter_column("course_id", existing_type=sa.Integer(), nullable=False)
    with op.batch_alter_table("concept") as batch:
        batch.alter_column("course_id", existing_type=sa.Integer(), nullable=False)


def downgrade():
    with op.batch_alter_table("concept") as batch:
        batch.alter_column("course_id", existing_type=sa.Integer(), nullable=True)
    with op.batch_alter_table("material") as batch:
        batch.alter_column("course_id", existing_type=sa.Integer(), nullable=True)
        batch.drop_column("error")
