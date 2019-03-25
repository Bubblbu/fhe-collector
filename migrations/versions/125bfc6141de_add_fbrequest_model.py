"""add FBRequest model

Revision ID: 125bfc6141de
Revises: ee7547dfc619
Create Date: 2019-03-25 19:24:28.539937

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '125bfc6141de'
down_revision = 'ee7547dfc619'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('fb_request',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('url_url', sa.String(length=512), nullable=False),
    sa.Column('response', sa.Text(), nullable=True),
    sa.Column('reactions', sa.Integer(), nullable=True),
    sa.Column('shares', sa.Integer(), nullable=True),
    sa.Column('comments', sa.Integer(), nullable=True),
    sa.Column('plugin_comments', sa.Integer(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['url_url'], ['url.url'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('fb_request')
    # ### end Alembic commands ###