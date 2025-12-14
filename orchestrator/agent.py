from google.adk.agents.llm_agent import Agent
from google.genai import types

from .tools import (
    run_sql_analysis_tool,
    get_db_knowledge_tool,
    save_integration_decision_tool
)

# --- Shared Instruction for Sub-Agents ---
# This ensures they act like functions, not chat bots.
NON_INTERACTIVE_INSTRUCTION = """
IMPORTANT: You are a processing engine, not a chat assistant. 
1. Perform your specific task immediately using your tools.
2. Output your findings concisely.
3. DO NOT ask the user "What would you like to do next?".
4. DO NOT ask for clarification. If data is missing, make a reasonable assumption or note the gap.
5. Terminate your turn immediately after reporting.
"""

# --- 1. Integration Sub-Agent ---
integration_agent = Agent(
    name="integration_agent",
    description="Calculates technical feasibility and equipment gaps.",
    instruction=f"""
    {NON_INTERACTIVE_INSTRUCTION}
    
    You are the Senior Bioprocess Engineer.
    Task:
    1. Query database for required equipment vs client inventory.
    2. List EXACTLY which machines are missing.
    3. Return the list of missing items to the root agent.
    """,
    tools=[run_sql_analysis_tool, get_db_knowledge_tool],
)

# --- 2. Economics Sub-Agent ---
economics_agent = Agent(
    name="economics_agent",
    description="Calculates costs and ROI.",
    instruction=f"""
    {NON_INTERACTIVE_INSTRUCTION}
    
    You are the Financial Analyst.
    Task:
    1. Take the technical gaps identified by the previous agent.
    2. Query database for costs of missing equipment.
    3. Calculate total CapEx and OpEx.
    4. Return the final ROI numbers.
    """,
    tools=[run_sql_analysis_tool, get_db_knowledge_tool],
)

# --- 3. Regulatory Sub-Agent ---
regulatory_agent = Agent(
    name="regulatory_agent",
    description="Checks legal compliance.",
    instruction=f"""
    {NON_INTERACTIVE_INSTRUCTION}
    
    You are the Regulatory Specialist.
    Task:
    1. Check database for regional compliance rules (GRAS, Novel Food).
    2. Return a Pass/Fail assessment and specific legal hurdles.
    """,
    tools=[run_sql_analysis_tool],
)

# --- 4. Quality Sub-Agent ---
quality_agent = Agent(
    name="quality_agent",
    description="Checks quality standards.",
    instruction=f"""
    {NON_INTERACTIVE_INSTRUCTION}
    
    You are the QA Manager.
    Task:
    1. Define sterility and purity requirements found in the database.
    2. Return a summary of quality risks.
    """,
    tools=[run_sql_analysis_tool],
)

# --- 5. Risk Sub-Agent ---
risk_agent = Agent(
    name="risk_agent",
    description="Analyzes strategic risks.",
    instruction=f"""
    {NON_INTERACTIVE_INSTRUCTION}
    
    You are the Risk Strategist.
    Task:
    1. Identify supply chain or market risks.
    2. Return a bulleted list of high-level risks.
    """,
    tools=[],
)

# --- Root Agent (Orchestrator) ---
root_agent = Agent(
    model='gemini-2.0-flash-exp',
    name='root_agent',
    instruction="""
      You are the "Precision Fermentation Integration Architect".
      
      CRITICAL OPERATIONAL MODE:
      - You must execute the ENTIRE workflow below AUTOMATICALLY.
      - DO NOT stop to ask the user for confirmation between steps.
      - DO NOT stop to ask "Should I continue?".
      - If a sub-agent returns data, immediately proceed to the next step.
      
      Your Workflow:
      1. Receive user request.
      2. Call 'integration_agent' to get technical gaps.
      3. Call 'economics_agent' (pass the gaps) to get ROI.
      4. Call 'regulatory_agent', 'quality_agent', and 'risk_agent' sequentially for their reports.
      5. Synthesize ALL findings into a final recommendation.
      6. CALL 'save_integration_decision_tool' to write to the DB.
      7. ONLY THEN, output the final summary to the user.
      
      Start immediately.
    """,
    sub_agents=[
        integration_agent,
        economics_agent,
        regulatory_agent,
        quality_agent,
        risk_agent
    ],
    tools=[save_integration_decision_tool],
    generate_content_config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.OFF,
            ),
        ]
    ),
)
