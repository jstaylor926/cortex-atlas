"""
Settings API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from ..database import get_db_connection
import json

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsData(BaseModel):
    """Settings data model"""
    ai: Optional[Dict[str, Any]] = None
    calendar: Optional[Dict[str, Any]] = None
    dev: Optional[Dict[str, Any]] = None
    ui: Optional[Dict[str, Any]] = None


@router.get("")
async def get_settings():
    """Get application settings"""
    conn = get_db_connection()
    cursor = conn.cursor()

    row = cursor.execute(
        "SELECT data FROM settings WHERE id = 1"
    ).fetchone()

    conn.close()

    if not row:
        # Return default settings if none exist
        return {
            "ai": {
                "openai_api_key": "",
                "chat_model": "gpt-4o-mini",
                "embedding_model": "text-embedding-3-large"
            },
            "calendar": {
                "google_connected": False,
                "selected_calendars": []
            },
            "dev": {
                "default_test_command": "pytest",
                "default_shell": "/bin/zsh"
            },
            "ui": {
                "theme": "system",
                "editor_font_size": 14
            }
        }

    return json.loads(row['data'])


@router.put("")
async def update_settings(settings: SettingsData):
    """Update application settings"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get existing settings
    existing = cursor.execute(
        "SELECT data FROM settings WHERE id = 1"
    ).fetchone()

    if existing:
        existing_data = json.loads(existing['data'])
    else:
        existing_data = {}

    # Merge with updates
    if settings.ai is not None:
        existing_data['ai'] = {**existing_data.get('ai', {}), **settings.ai}
    if settings.calendar is not None:
        existing_data['calendar'] = {**existing_data.get('calendar', {}), **settings.calendar}
    if settings.dev is not None:
        existing_data['dev'] = {**existing_data.get('dev', {}), **settings.dev}
    if settings.ui is not None:
        existing_data['ui'] = {**existing_data.get('ui', {}), **settings.ui}

    now = datetime.now().isoformat()
    new_data = json.dumps(existing_data)

    if existing:
        cursor.execute(
            "UPDATE settings SET data = ?, updated_at = ? WHERE id = 1",
            (new_data, now)
        )
    else:
        cursor.execute(
            "INSERT INTO settings (id, data, updated_at) VALUES (1, ?, ?)",
            (new_data, now)
        )

    conn.commit()
    conn.close()

    return existing_data
