"""fix issue: increase string length of source in Import() class to 500

Revision ID: 2efa047fe343
Revises: 4a3a663ce25d
Create Date: 2019-03-05 00:30:15.707276

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2efa047fe343'
down_revision = '4a3a663ce25d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('import', 'source',
               existing_type=sa.VARCHAR(length=32),
               type_=sa.String(length=500),
               existing_nullable=True)
    op.alter_column('url', 'url',
               existing_type=sa.VARCHAR(length=256),
               type_=sa.String(length=512))
    op.alter_column('url', 'url_type',
               existing_type=sa.VARCHAR(length=64),
               type_=sa.String(length=32),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('url', 'url_type',
               existing_type=sa.String(length=32),
               type_=sa.VARCHAR(length=64),
               existing_nullable=True)
    op.alter_column('url', 'url',
               existing_type=sa.String(length=512),
               type_=sa.VARCHAR(length=256))
    op.alter_column('import', 'source',
               existing_type=sa.String(length=500),
               type_=sa.VARCHAR(length=32),
               existing_nullable=True)
    # ### end Alembic commands ###