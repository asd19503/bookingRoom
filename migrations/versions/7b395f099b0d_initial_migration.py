"""Initial migration

Revision ID: 7b395f099b0d
Revises: 
Create Date: 2024-11-27 08:40:23.709613

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7b395f099b0d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('room')
    with op.batch_alter_table('booking', schema=None) as batch_op:
        batch_op.alter_column('booking_name',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)
        batch_op.alter_column('department',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)
        batch_op.alter_column('chairman',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)
        batch_op.alter_column('start_time',
               existing_type=sa.VARCHAR(length=20),
               nullable=False)
        batch_op.alter_column('end_time',
               existing_type=sa.VARCHAR(length=20),
               nullable=False)
        batch_op.alter_column('reservation_date',
               existing_type=sa.VARCHAR(length=20),
               type_=sa.String(length=10),
               nullable=False)
        batch_op.alter_column('room_name',
               existing_type=sa.VARCHAR(length=30),
               type_=sa.String(length=100),
               nullable=False)
        batch_op.alter_column('username',
               existing_type=sa.VARCHAR(length=50),
               nullable=False)
        batch_op.drop_constraint('fk_username', type_='foreignkey')

    with op.batch_alter_table('user_table', schema=None) as batch_op:
        batch_op.alter_column('role',
               existing_type=sa.VARCHAR(length=20),
               type_=sa.String(length=50),
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_table', schema=None) as batch_op:
        batch_op.alter_column('role',
               existing_type=sa.String(length=50),
               type_=sa.VARCHAR(length=20),
               existing_nullable=False)

    with op.batch_alter_table('booking', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_username', 'user_table', ['username'], ['username'], ondelete='CASCADE')
        batch_op.alter_column('username',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)
        batch_op.alter_column('room_name',
               existing_type=sa.String(length=100),
               type_=sa.VARCHAR(length=30),
               nullable=True)
        batch_op.alter_column('reservation_date',
               existing_type=sa.String(length=10),
               type_=sa.VARCHAR(length=20),
               nullable=True)
        batch_op.alter_column('end_time',
               existing_type=sa.VARCHAR(length=20),
               nullable=True)
        batch_op.alter_column('start_time',
               existing_type=sa.VARCHAR(length=20),
               nullable=True)
        batch_op.alter_column('chairman',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)
        batch_op.alter_column('department',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)
        batch_op.alter_column('booking_name',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)

    op.create_table('room',
    sa.Column('room_id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('room_name', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('room_id', name='room_pkey')
    )
    # ### end Alembic commands ###
