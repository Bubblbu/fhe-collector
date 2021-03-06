"""re-factor models

Revision ID: 947aad10a260
Revises: f6102dc58c7f
Create Date: 2019-08-14 17:48:21.473827

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '947aad10a260'
down_revision = 'f6102dc58c7f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('doi', sa.Column('doi_lp_url', sa.Boolean(), nullable=False))
    op.add_column('doi', sa.Column('doi_new_url', sa.Boolean(), nullable=False))
    op.add_column('doi', sa.Column('doi_old_url', sa.Boolean(), nullable=False))
    op.add_column('doi', sa.Column('pm_url', sa.Boolean(), nullable=False))
    op.add_column('doi', sa.Column('pmc_url', sa.Boolean(), nullable=False))
    op.add_column('doi', sa.Column('unpaywall_url', sa.Boolean(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('doi', 'unpaywall_url')
    op.drop_column('doi', 'pmc_url')
    op.drop_column('doi', 'pm_url')
    op.drop_column('doi', 'doi_old_url')
    op.drop_column('doi', 'doi_new_url')
    op.drop_column('doi', 'doi_lp_url')
    # ### end Alembic commands ###
