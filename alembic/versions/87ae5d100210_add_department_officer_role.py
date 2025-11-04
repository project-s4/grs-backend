"""add_department_officer_role

Revision ID: 87ae5d100210
Revises: 702423e2d06b
Create Date: 2025-11-04 17:46:19.509045

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '87ae5d100210'
down_revision: Union[str, None] = '702423e2d06b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add 'department_officer' to the userrole enum if it doesn't exist
    # Note: PostgreSQL doesn't support IF NOT EXISTS for enum values directly
    # So we check if it exists first, and if not, add it
    connection = op.get_bind()
    
    # Check if 'department_officer' already exists in the enum
    result = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 
            FROM pg_enum 
            WHERE enumlabel = 'department_officer' 
            AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'userrole')
        )
    """))
    
    exists = result.scalar()
    
    if not exists:
        # Add the enum value (PostgreSQL 9.1+)
        # Note: This must be run outside a transaction block
        op.execute(sa.text("ALTER TYPE userrole ADD VALUE 'department_officer'"))


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum type, which is complex
    # For now, we'll leave the enum value in place
    # If you need to remove it, you would need to:
    # 1. Update all users with department_officer role to another role
    # 2. Recreate the enum type without department_officer
    pass
