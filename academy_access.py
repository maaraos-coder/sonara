"""Server-side bridge between SONARA and the Diplomado roster.

Only the Supabase service-role/secret key may be used here.  The key is read
from deployment secrets and is never sent to the browser or stored in Git.
"""

from __future__ import annotations

import os

import streamlit as st

try:
    from supabase import create_client
except ImportError:  # Allows SONARA to keep rendering with a clear fallback.
    create_client = None


DIPLOMADO_COURSE_ID = "diplomado-acustica-edificacion"


def _secret(name: str, fallback: str = "") -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    try:
        config = st.secrets["supabase"]
        return str(config.get(fallback, "") or "").strip()
    except (KeyError, FileNotFoundError, TypeError, ValueError):
        return ""


@st.cache_resource(show_spinner=False)
def academy_supabase_client():
    """Create a private server-side client, or return None if not configured."""
    if create_client is None:
        return None
    url = _secret("SONARA_ACADEMY_SUPABASE_URL", "url")
    key = (
        _secret("SONARA_ACADEMY_SUPABASE_SERVICE_ROLE_KEY", "service_role_key")
        or _secret("SONARA_ACADEMY_SUPABASE_SECRET_KEY", "secret_key")
    )
    # Never silently fall back to a publishable/anonymous key: the roster is
    # intentionally protected by RLS and must only be queried server-side.
    if not url or not key or key.startswith("sb_publishable_"):
        return None
    try:
        return create_client(url, key)
    except Exception:
        return None


@st.cache_data(ttl=300, show_spinner=False)
def academy_student_by_email(email: str):
    """Return the active roster entry for an email, without exposing the roster."""
    normalized = str(email or "").strip().lower()
    if not normalized or "@" not in normalized or len(normalized) > 254:
        return None
    client = academy_supabase_client()
    if client is None:
        return None
    try:
        rows = (
            client.table("authorized_students")
            .select("display_name,email,course_id,active")
            .eq("course_id", DIPLOMADO_COURSE_ID)
            .eq("email", normalized)
            .eq("active", True)
            .limit(1)
            .execute()
            .data
            or []
        )
    except Exception:
        return None
    return rows[0] if rows else None


def academy_bridge_configured() -> bool:
    return academy_supabase_client() is not None
