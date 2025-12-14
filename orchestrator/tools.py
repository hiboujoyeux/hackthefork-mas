import json
from .database import get_schema_summary, execute_read_query, persist_study_results


def get_db_knowledge_tool():
    """
    Returns the full database schema so the agent knows how to write SQL.
    """
    return get_schema_summary()


def run_sql_analysis_tool(query: str):
    """
    Executes a read-only SQL query to analyze matches, costs, or regulatory rules.
    Input: Valid SQLite SELECT string.
    """
    return execute_read_query(query)


def save_integration_decision_tool(json_input: str):
    """
    Persists the final decision to the database.
    Expected JSON string format:
    {
      "site_id": 1,
      "line_id": 2,
      "process_id": "PF-001",
      "overall_fit": "High",
      "risk_level": "Medium",
      "recommendations": [
         {"type": "machine_upgrade", "content": {"machine": "Fermenter", "action": "Replace"}}
      ]
    }
    """
    try:
        data = json.loads(json_input)
        return persist_study_results(
            site_id=data['site_id'],
            line_id=data['line_id'],
            process_id=data['process_id'],
            fit_analysis=data['overall_fit'],
            risk_level=data['risk_level'],
            recommendations=data.get('recommendations', [])
        )
    except Exception as e:
        return f"Tool Error: {str(e)}"
