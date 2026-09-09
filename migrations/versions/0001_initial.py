from alembic import op
import sqlalchemy as sa

revision='0001_initial'
down_revision=None
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('users',sa.Column('id',sa.Integer(),primary_key=True),sa.Column('telegram_id',sa.BigInteger(),nullable=False),sa.Column('username',sa.String(255)),sa.Column('first_name',sa.String(255)),sa.Column('is_admin',sa.Boolean(),nullable=False,server_default=sa.false()),sa.Column('created_at',sa.DateTime(),nullable=False),sa.Column('last_active',sa.DateTime(),nullable=False))
    op.create_index('ix_users_telegram_id','users',['telegram_id'],unique=True)
    op.create_table('animes',sa.Column('id',sa.Integer(),primary_key=True),sa.Column('title',sa.String(500),nullable=False),sa.Column('alternate_title',sa.String(500)),sa.Column('description',sa.Text()),sa.Column('poster',sa.String(1000)),sa.Column('genre',sa.String(500)),sa.Column('year',sa.Integer()),sa.Column('status',sa.String(50),nullable=False),sa.Column('created_at',sa.DateTime(),nullable=False),sa.Column('updated_at',sa.DateTime(),nullable=False))
    op.create_index('ix_animes_title','animes',['title']); op.create_index('ix_animes_alternate_title','animes',['alternate_title']); op.create_index('ix_animes_genre','animes',['genre'])
    op.create_table('episodes',sa.Column('id',sa.Integer(),primary_key=True),sa.Column('anime_id',sa.Integer(),sa.ForeignKey('animes.id',ondelete='CASCADE'),nullable=False),sa.Column('episode_number',sa.Integer(),nullable=False),sa.Column('telegram_file_id',sa.String(1000),nullable=False),sa.Column('file_unique_id',sa.String(500)),sa.Column('caption',sa.Text()),sa.Column('views',sa.Integer(),nullable=False),sa.Column('created_at',sa.DateTime(),nullable=False),sa.Column('updated_at',sa.DateTime(),nullable=False),sa.UniqueConstraint('anime_id','episode_number',name='uq_episode_anime_number'))
    op.create_index('ix_episode_anime_number','episodes',['anime_id','episode_number']); op.create_index('ix_episodes_file_unique_id','episodes',['file_unique_id'])
    op.create_table('favorites',sa.Column('user_id',sa.Integer(),sa.ForeignKey('users.id',ondelete='CASCADE'),primary_key=True),sa.Column('anime_id',sa.Integer(),sa.ForeignKey('animes.id',ondelete='CASCADE'),primary_key=True),sa.Column('created_at',sa.DateTime(),nullable=False))
    op.create_table('watch_progress',sa.Column('user_id',sa.Integer(),sa.ForeignKey('users.id',ondelete='CASCADE'),primary_key=True),sa.Column('anime_id',sa.Integer(),sa.ForeignKey('animes.id',ondelete='CASCADE'),primary_key=True),sa.Column('episode_number',sa.Integer(),nullable=False),sa.Column('updated_at',sa.DateTime(),nullable=False))

def downgrade():
    op.drop_table('watch_progress'); op.drop_table('favorites'); op.drop_index('ix_episode_anime_number',table_name='episodes'); op.drop_table('episodes'); op.drop_index('ix_animes_genre',table_name='animes'); op.drop_index('ix_animes_alternate_title',table_name='animes'); op.drop_index('ix_animes_title',table_name='animes'); op.drop_table('animes'); op.drop_index('ix_users_telegram_id',table_name='users'); op.drop_table('users')
