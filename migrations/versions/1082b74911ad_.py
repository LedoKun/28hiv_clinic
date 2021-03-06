"""empty message

Revision ID: 1082b74911ad
Revises: e1b42649b083
Create Date: 2019-06-14 09:54:28.917558

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1082b74911ad'
down_revision = 'e1b42649b083'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('patient', sa.Column('education', sa.Unicode(), nullable=True))
    op.add_column('patient', sa.Column('occupation', sa.Unicode(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('patient', 'occupation')
    op.drop_column('patient', 'education')
    # ### end Alembic commands ###
