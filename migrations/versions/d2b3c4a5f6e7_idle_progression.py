"""Add idle progression fields to users."""

from alembic import op
import sqlalchemy as sa

revision = "d2b3c4a5f6e7"
down_revision = "5e7b2e72e6f2"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("plot_level", sa.Integer(), nullable=False, server_default="1"))
        batch_op.add_column(sa.Column("seed_tier", sa.Integer(), nullable=False, server_default="1"))
        batch_op.add_column(sa.Column("farmkeeper_level", sa.Integer(), nullable=False, server_default="0"))


def downgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("farmkeeper_level")
        batch_op.drop_column("seed_tier")
        batch_op.drop_column("plot_level")
