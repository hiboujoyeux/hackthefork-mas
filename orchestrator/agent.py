from google.adk.agents.llm_agent import Agent
from google.genai import types

# Import tools defined in tools.py
# We assume these exist based on your previous single-agent implementation
from .tools import (
    run_sql_analysis_tool,
    get_db_knowledge_tool,
    save_integration_decision_tool
)

# --- 1. Integration Sub-Agent ---
integration_agent = Agent(
    name="integration_agent",
    description="Responsible for technical feasibility, equipment matching, and process design.",
    instruction="""
    You are a Senior Bioprocess Engineer.
    Your goal is to determine if the transition to Precision Fermentation is technically feasible.
    
    Responsibilities:
    1. Identify biological requirements (Host Strain, Unit Operations) using SQL tools.
    2. Compare Client Equipment vs. Required Equipment.
    3. Identify missing equipment (CapEx requirements).
    
    Use the 'run_sql_analysis_tool' to query the database for machine specs and client inventories.
    """,
    tools=[run_sql_analysis_tool, get_db_knowledge_tool],
)

# --- 2. Economics Sub-Agent ---
economics_agent = Agent(
    name="economics_agent",
    description="Responsible for financial analysis, OpEx, CapEx, and ROI calculations.",
    instruction="""
    You are a Financial Analyst specializing in bio-manufacturing.
    Your goal is to calculate the cost implications of the transition.
    
    Responsibilities:
    1. Calculate the cost of missing equipment (CapEx).
    2. Estimate Operational Expenses (OpEx) based on utility and feedstock costs.
    3. Compare current animal-based costs vs. fermentation costs to determine ROI.
    
    Use the 'run_sql_analysis_tool' to query the database for equipment prices and utility costs.
    """,
    tools=[run_sql_analysis_tool, get_db_knowledge_tool],
)

# --- 3. Regulatory Sub-Agent ---
regulatory_agent = Agent(
    name="regulatory_agent",
    description="Responsible for legal compliance, FDA/EFSA regulations, and Novel Foods.",
    instruction="""
    You are a Regulatory Affairs Specialist.
    Your goal is to identify the legal hurdles of introducing this fermentation product.
    
    Responsibilities:
    1. Assess GRAS (Generally Recognized As Safe) status of the host organism.
    2. Outline requirements for Novel Food applications (EU) or FDA filings (USA).
    3. Advise on labeling requirements.
    """,
    tools=[run_sql_analysis_tool],
)

# --- 4. Quality Sub-Agent ---
quality_agent = Agent(
    name="quality_agent",
    description="Responsible for product standards, purity, and sterility assurance.",
    instruction="""
    You are a Quality Assurance Manager.
    Your goal is to ensure the proposed process meets industrial standards.
    
    Responsibilities:
    1. Define sterility requirements for the fermentation process.
    2. Establish Quality Control (QC) checkpoints.
    3. Assess the risk of product variability compared to animal-derived ingredients.
    """,
    tools=[run_sql_analysis_tool],
)

# --- 5. Risk Sub-Agent ---
risk_agent = Agent(
    name="risk_agent",
    description="Responsible for supply chain, biological, and market risks.",
    instruction="""
    You are a Strategic Risk Assessor.
    Your goal is to identify what could go wrong.
    
    Responsibilities:
    1. Analyze supply chain risks (e.g., single-source feedstock).
    2. Analyze biological risks (contamination, phage attacks).
    3. Analyze market adoption risks.
    
    Provide a high-level risk mitigation strategy.
    """,
    tools=[],
)

# --- Root Agent (Orchestrator) ---
root_agent = Agent(
    model='gemini-2.0-flash-exp',
    name='root_agent',
    instruction="""
      You are the "Precision Fermentation Integration Architect".
      You are the Project Manager orchestrating a feasibility study for a client wanting to switch from animal ingredients to fermentation.
      
      You manage a team of experts. Your workflow is:
      1. Receive the user's request (context and budget).
      2. Delegate technical analysis to the 'integration_agent'.
      3. Delegate cost analysis to the 'economics_agent' (pass them the technical gaps found).
      4. Consult 'regulatory_agent', 'quality_agent', and 'risk_agent' for compliance and safety aspects.
      5. Synthesize all findings into a final recommendation (Go or No-Go).
      6. Use the 'save_integration_decision_tool' to save the final verdict to the database.
      
      Rules:
      - Do not make up technical data; ask the Integration Agent.
      - Do not guess costs; ask the Economics Agent.
      - Always prioritize User Input over Database limits (Hierarchy of Truth).
    """,
    global_instruction=(
        "You are the Bio-Integration Architect. You orchestrate a team of agents to validate fermentation projects."
    ),
    sub_agents=[
        integration_agent,
        economics_agent,
        regulatory_agent,
        quality_agent,
        risk_agent
    ],
    # The root agent keeps the tool to save the final report
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
