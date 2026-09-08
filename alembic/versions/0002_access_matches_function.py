"""add access_matches function

Revision ID: 0002
Revises: 0001
Create Date: 2025-01-02 00:00:00
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    CREATE OR REPLACE FUNCTION rag.access_matches(
        policy jsonb,
        user_role text,
        user_projects text[],
        user_id uuid
    ) RETURNS boolean AS $$
    DECLARE
        allowed_roles text[];
        allowed_projects text[];
        allowed_users uuid[];
    BEGIN
        IF policy IS NULL OR policy = '{}'::jsonb THEN
            RETURN true;
        END IF;

        allowed_roles := COALESCE(
            (SELECT array_agg(e::text) FROM jsonb_array_elements_text(policy->'roles') e),
            ARRAY[]::text[]
        );
        allowed_projects := COALESCE(
            (SELECT array_agg(e::text) FROM jsonb_array_elements_text(policy->'projects') e),
            ARRAY[]::text[]
        );
        allowed_users := COALESCE(
            (SELECT array_agg(e::uuid) FROM jsonb_array_elements_text(policy->'users') e),
            ARRAY[]::uuid[]
        );

        IF user_role = 'administrator' THEN
            RETURN true;
        END IF;

        IF user_id = ANY(allowed_users) THEN
            RETURN true;
        END IF;

        IF user_role = ANY(allowed_roles) THEN
            RETURN true;
        END IF;

        IF array_length(allowed_projects, 1) > 0 AND user_projects && allowed_projects THEN
            RETURN true;
        END IF;

        RETURN false;
    END;
    $$ LANGUAGE plpgsql IMMUTABLE SECURITY DEFINER;
    """)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS rag.access_matches(jsonb, text, text[], uuid)")
