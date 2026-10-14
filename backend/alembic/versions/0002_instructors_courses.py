"""add instructors, courses, and course ownership"""
from alembic import op
import sqlalchemy as sa

revision = "0002_instructors_courses"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "instructor",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_instructor_email", "instructor", ["email"], unique=True)
    op.create_table(
        "course",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("instructor_id", sa.Integer(), sa.ForeignKey("instructor.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("class_size", sa.Integer(), nullable=True),
        sa.Column("join_code", sa.String(), nullable=False),
        sa.Column("joining_open", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_course_instructor_id", "course", ["instructor_id"])
    op.create_index("ix_course_join_code", "course", ["join_code"], unique=True)
    for table in ("concept", "material", "student", "message", "quizitem", "quizresponse", "verdict"):
        with op.batch_alter_table(table) as batch:
            batch.add_column(sa.Column("course_id", sa.Integer(), nullable=True))
            batch.create_foreign_key(f"fk_{table}_course_id", "course", ["course_id"], ["id"])
            batch.create_index(f"ix_{table}_course_id", ["course_id"])


def downgrade():
    for table in ("verdict", "quizresponse", "quizitem", "message", "student", "material", "concept"):
        with op.batch_alter_table(table) as batch:
            batch.drop_index(f"ix_{table}_course_id")
            batch.drop_constraint(f"fk_{table}_course_id", type_="foreignkey")
            batch.drop_column("course_id")
    op.drop_index("ix_course_join_code", table_name="course")
    op.drop_index("ix_course_instructor_id", table_name="course")
    op.drop_table("course")
    op.drop_index("ix_instructor_email", table_name="instructor")
    op.drop_table("instructor")
