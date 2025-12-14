from google.adk.agents.llm_agent import Agent
from google.adk.tools import AgentTool
from google.genai import types

# Import the base tools
from .tools import (
    run_sql_analysis_tool,
    get_db_knowledge_tool,
    save_integration_decision_tool
)

# ==========================================
# 0. PROTOCOLS
# ==========================================
FAIL_FORWARD_PROTOCOL = """
CRITICAL EXECUTION RULES:
1. **Goal**: Provide a result. Never return "I don't know".
2. **Rescue Clause**: If the database is missing data/tables, use your Internal Knowledge to estimate.
3. **Format**: Output your findings clearly.
"""

# ==========================================
# 1. DEFINE SUB-AGENTS (The Workers)
# ==========================================
# We stick with Flash for the workers for speed/efficiency.

integration_agent = Agent(
    model='gemini-2.0-flash-exp',
    name="integration_agent",
    description="Analyzes technical feasibility.",
    instruction=f"""
    {FAIL_FORWARD_PROTOCOL}
    You are a Senior Bioprocess Engineer.
    Task: Recommend a Host Strain/Process and identify missing equipment.
    *Fallback*: If DB inventory is unreadable, assume client has NO equipment.
    """,
    tools=[run_sql_analysis_tool, get_db_knowledge_tool],
)

economics_agent = Agent(
    model='gemini-2.0-flash-exp',
    name="economics_agent",
    description="Calculates ROI.",
    instruction=f"""
    {FAIL_FORWARD_PROTOCOL}
    You are a Financial Analyst.
    Task: Calculate CapEx and ROI based on missing equipment.
    *Fallback*: Use default cost $500k per major unit if DB has no prices.
    """,
    tools=[run_sql_analysis_tool, get_db_knowledge_tool],
)

regulatory_agent = Agent(
    model='gemini-2.0-flash-exp',
    name="regulatory_agent",
    description="Checks compliance.",
    instruction=f"""
    {FAIL_FORWARD_PROTOCOL}
    You are a Regulatory Specialist.
    Task: Check GRAS/Novel Food rules.
    *Fallback*: Use standard FDA/EFSA knowledge if table missing.
    """,
    tools=[run_sql_analysis_tool, get_db_knowledge_tool],
)

quality_agent = Agent(
    model='gemini-2.0-flash-exp',
    name="quality_agent",
    description="Checks quality.",
    instruction=f"""
    {FAIL_FORWARD_PROTOCOL}
    You are a QA Manager.
    Task: Define sterility requirements.
    *Fallback*: Assume Pharma-Grade requirements.
    """,
    tools=[run_sql_analysis_tool, get_db_knowledge_tool],
)

# --- RISK AGENT (The Trigger) ---
risk_agent = Agent(
    model='gemini-2.0-flash-exp',
    name="risk_agent",
    description="Analyzes strategic risks.",
    instruction=f"""
    {FAIL_FORWARD_PROTOCOL}
    You are a Risk Strategist.
    
    Task: Identify strategic risks.
    
    IMPORTANT FINAL STEP:
    You are the LAST agent in the chain.
    You MUST end your response with this exact text:
    "## DATA COLLECTION COMPLETE. ORCHESTRATOR: EXECUTE SAVING PROTOCOL NOW. ##"
    """,
    tools=[],
)

# ==========================================
# 2. WRAP AGENTS AS TOOLS
# ==========================================

integration_tool = AgentTool(agent=integration_agent)
economics_tool = AgentTool(agent=economics_agent)
regulatory_tool = AgentTool(agent=regulatory_agent)
quality_tool = AgentTool(agent=quality_agent)
risk_tool = AgentTool(agent=risk_agent)

# ==========================================
# 3. ROOT AGENT (The Orchestrator)
# ==========================================

# Using the latest model for superior reasoning and instruction following
ORCHESTRATOR_MODEL = 'gemini-3-pro-preview'

root_agent = Agent(
    model=ORCHESTRATOR_MODEL,
    name="root_agent",
    description="Precision Fermentation Integration Architect",
    instruction="""
      You are the "Precision Fermentation Integration Architect".
      
      ### MISSION CHECKLIST (You MUST complete all 6 items)
      [ ] 1. Technical Analysis (Integration Agent)
      [ ] 2. Financial Analysis (Economics Agent)
      [ ] 3. Regulatory Check (Regulatory Agent)
      [ ] 4. Quality Check (Quality Agent)
      [ ] 5. Risk Assessment (Risk Agent)
      [ ] 6. ARCHIVE & REPORT (Save Tool + Final Summary)
      
      ### EXECUTION RULES
      1. **Chain of Thought**: You must narrate your steps (e.g., "Step 1 complete, moving to Step 2...").
      2. **The Risk Trigger**: When the `risk_agent` says "EXECUTE SAVING PROTOCOL", you must IMMEDIATELY perform Step 6.
      3. **Failure Condition**: If you stop after Step 5, you have FAILED the mission.
      
      ### STEP 6 INSTRUCTIONS (Mandatory)
      1. Call `save_integration_decision_tool` with the final "Go/No-Go" decision.
      2. Output the report in the Markdown format below.

      --- FINAL REPORT TEMPLATE ---
      
      # 🧬 1. Technical Process Overview
      > **Process:** [Name] | **Host:** [Species]
      *   **Mechanism:** [Summary]
      *   **Key Operations:** [Upstream -> Downstream]

      # 🏗️ 2. Implementation & CapEx
      *   **Missing Equipment:**
          *   [List Gaps]
      *   **Total Investment Required:** **[CapEx Value]**

      # 💰 3. Economic Analysis (ROI)
      *   **Projected Production Cost:** [Value]
      *   **📉 Annual Cost Savings:** **[Savings Value]**

      # ✅ 4. Final Verdict
      *   **Decision:** [GO / NO-GO]
      *   **Reasoning:** [Summary]
    """,
    tools=[
        integration_tool,
        economics_tool,
        regulatory_tool,
        quality_tool,
        risk_tool,
        save_integration_decision_tool
    ],
    generate_content_config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.OFF,
            ),
        ]
    ),
)
