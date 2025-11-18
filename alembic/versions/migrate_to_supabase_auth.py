"""Migrate to Supabase Auth

Revision ID: migrate_to_supabase_auth
Revises: 87ae5d100210
Create Date: 2025-01-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'migrate_to_supabase_auth'
down_revision: Union[str, None] = '87ae5d100210'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # For fresh start: Clear existing users (since we're migrating to OAuth)
    # This is safe because user requested fresh start
    op.execute(sa.text("DELETE FROM users"))
    
    # Add supabase_user_id column (required for new auth system)
    op.add_column('users', sa.Column('supabase_user_id', postgresql.UUID(as_uuid=True), nullable=False))
    
    # Make email required (non-nullable) - Supabase requires email
    op.alter_column('users', 'email', nullable=False)
    
    # Create unique constraint on supabase_user_id
    op.create_unique_constraint('uq_users_supabase_user_id', 'users', ['supabase_user_id'])
    
    # Remove password-related columns
    op.drop_column('users', 'password_hash')
    op.drop_column('users', 'reset_token')
    op.drop_column('users', 'reset_token_expiry')


def downgrade() -> None:
    # Add back password-related columns
    op.add_column('users', sa.Column('password_hash', sa.String(), nullable=True))
    op.add_column('users', sa.Column('reset_token', sa.String(), nullable=True))
    op.add_column('users', sa.Column('reset_token_expiry', sa.DateTime(), nullable=True))
    
    # Remove unique constraint
    op.drop_constraint('uq_users_supabase_user_id', 'users', type_='unique')
    
    # Make email nullable again
    op.alter_column('users', 'email', nullable=True)
    
    # Remove supabase_user_id column
    op.drop_column('users', 'supabase_user_id')

