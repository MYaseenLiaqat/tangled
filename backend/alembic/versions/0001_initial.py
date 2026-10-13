"""initial schema"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("concept", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("key", sa.String(), nullable=False),
                   sa.Column("name", sa.String(), nullable=False), sa.Column("module", sa.String(), nullable=False),
                   sa.Column("description", sa.String(), nullable=False))
    op.create_index("ix_concept_key", "concept", ["key"], unique=True)
    op.create_table("material", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("filename", sa.String(), nullable=False),
                   sa.Column("kind", sa.String(), nullable=False), sa.Column("size_kb", sa.Integer(), nullable=False),
                   sa.Column("chunks", sa.Integer(), nullable=False), sa.Column("status", sa.String(), nullable=False))
    op.create_table("student", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("code", sa.String(), nullable=False))
    op.create_index("ix_student_code", "student", ["code"], unique=True)
    op.create_table("message", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("student_id", sa.Integer(), sa.ForeignKey("student.id"), nullable=False),
                   sa.Column("session_id", sa.String(), nullable=False), sa.Column("text", sa.String(), nullable=False), sa.Column("answer", sa.String(), nullable=False),
                   sa.Column("concept_id", sa.Integer(), sa.ForeignKey("concept.id")), sa.Column("similarity", sa.Float(), nullable=False),
                   sa.Column("intent", sa.String(), nullable=False), sa.Column("intent_conf", sa.Float(), nullable=False), sa.Column("misconception", sa.Boolean(), nullable=False),
                   sa.Column("phrase", sa.String(), nullable=False), sa.Column("feedback", sa.String(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_message_student_id", "message", ["student_id"])
    op.create_index("ix_message_concept_id", "message", ["concept_id"])
    op.create_index("ix_message_created_at", "message", ["created_at"])
    op.create_table("quizitem", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("key", sa.String(), nullable=False),
                   sa.Column("concept_id", sa.Integer(), sa.ForeignKey("concept.id"), nullable=False))
    op.create_index("ix_quizitem_key", "quizitem", ["key"], unique=True)
    op.create_table("quizresponse", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("item_id", sa.Integer(), sa.ForeignKey("quizitem.id"), nullable=False),
                   sa.Column("student_id", sa.Integer(), sa.ForeignKey("student.id"), nullable=False), sa.Column("option", sa.String(), nullable=False), sa.Column("correct", sa.Boolean(), nullable=False))
    op.create_index("ix_quizresponse_item_id", "quizresponse", ["item_id"])
    op.create_table("verdict", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("concept_id", sa.Integer(), sa.ForeignKey("concept.id"), nullable=False),
                   sa.Column("verdict", sa.String(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_verdict_concept_id", "verdict", ["concept_id"])

def downgrade():
    for table in ("verdict", "quizresponse", "quizitem", "message", "student", "material", "concept"):
        op.drop_table(table)
