"""Add voicemail detection fields to call_logs

Revision ID: voicemail_detection_001
Revises: 8e9299eec4ce
Create Date: 2024-07-17 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'voicemail_detection_001'
down_revision = '8e9299eec4ce'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add voicemail detection fields to call_logs table
    op.add_column('call_logs', sa.Column('voicemail_detection_confidence', sa.Float(), nullable=True))
    op.add_column('call_logs', sa.Column('detection_metadata', sa.JSON(), nullable=True))
    op.add_column('call_logs', sa.Column('voicemail_message_left', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('call_logs', sa.Column('beep_detected_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove voicemail detection fields from call_logs table
    op.drop_column('call_logs', 'beep_detected_at')
    op.drop_column('call_logs', 'voicemail_message_left')
    op.drop_column('call_logs', 'detection_metadata')
    op.drop_column('call_logs', 'voicemail_detection_confidence') 