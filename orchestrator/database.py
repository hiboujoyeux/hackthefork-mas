import sqlite3
import json
import os
from pathlib import Path
from typing import List, Dict, Any

# ==========================================
# PATH CONFIGURATION
# ==========================================
# Get the directory where this file (database.py) is located: .../hackthefork/my_agent
CURRENT_DIR = Path(__file__).parent.resolve()

# Go up one level to find the database: .../hackthefork/pf_database.db
DB_PATH = CURRENT_DIR.parent / "pf_database.db"


def get_connection():
    """Establishes a connection to the SQLite database."""
    # Debug print to help you see where it is looking in the logs
    if not DB_PATH.exists():
        print(f"CRITICAL ERROR: Database not found at: {DB_PATH}")

    return sqlite3.connect(str(DB_PATH))

# ==========================================
# TOOL FUNCTIONS
# ==========================================


def get_schema_summary() -> str:
    """Returns a text summary of all CREATE TABLE statements to help the LLM."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Get all table names
        cursor.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        if not tables:
            return "Error: Connected to database, but found no tables. Is the DB initialized?"

        schema_text = "DATABASE SCHEMA:\n"
        for name, sql in tables:
            # Clean up None values if any
            sql_text = sql if sql else "No Schema Definition"
            schema_text += f"--- TABLE: {name} ---\n{sql_text}\n\n"

        conn.close()
        return schema_text
    except Exception as e:
        return f"Database Connection Error: {str(e)} at path {DB_PATH}"


def execute_read_query(sql: str) -> str:
    """Executes a SELECT query and returns JSON string results."""
    # Basic safety check
    if not sql.strip().upper().startswith("SELECT"):
        return "Error: Only SELECT queries are allowed in this tool."

    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row  # Allow column access by name
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()

        # Convert to list of dicts
        result = [dict(row) for row in rows]
        conn.close()

        if not result:
            return "Query executed successfully but returned 0 results."

        return json.dumps(result, indent=2)
    except Exception as e:
        return f"SQL Error: {str(e)}"


def persist_study_results(site_id: int, line_id: int, process_id: str,
                          fit_analysis: str, risk_level: str,
                          recommendations: List[Dict]) -> str:
    """Writes the final synthesis to the integration tables."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 1. Insert Main Study
        cursor.execute("""
            INSERT INTO integration_study (site_id, line_id, process_id, overall_fit, overall_risk_level)
            VALUES (?, ?, ?, ?, ?) RETURNING study_id
        """, (site_id, line_id, process_id, fit_analysis, risk_level))

        study_id = cursor.fetchone()[0]

        # 2. Insert Recommendations
        for rec in recommendations:
            cursor.execute("""
                INSERT INTO integration_recommendation (study_id, recommendation_type, content_json)
                VALUES (?, ?, ?)
            """, (study_id, rec.get('type', 'general'), json.dumps(rec.get('content', {}))))

        conn.commit()
        conn.close()
        return f"Success: Integration Study saved with ID {study_id}."
    except Exception as e:
        return f"Db Write Error: {str(e)}"
