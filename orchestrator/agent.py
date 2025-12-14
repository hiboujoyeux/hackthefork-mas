import random

from google.adk.agents.llm_agent import Agent
# from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH
# from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
# from google.adk.tools.example_tool import ExampleTool
from google.genai import types


# --- Roll Die Sub-Agent ---
def roll_die(sides: int) -> int:
    """Roll a die and return the rolled result."""
    return random.randint(1, sides)


roll_agent = Agent(
    name="roll_agent",
    description="Handles rolling dice of different sizes.",
    instruction="""
      You are responsible for rolling dice based on the user's request.
      When asked to roll a die, you must call the roll_die tool with the number of sides as an integer.
    """,
    tools=[roll_die],
    generate_content_config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(  # avoid false alarm about rolling dice.
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.OFF,
            ),
        ]
    ),
)

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    instruction="""
      You are a helpful assistant that can roll dice when asked to.
      You delegate rolling dice tasks to the roll_agent.
      Follow these steps:
      1. If the user asks to roll a die, delegate to the roll_agent.
      2. If the user asks any other question, answer it.
      Always clarify the results before proceeding.
    """,
    global_instruction=(
        "You are DiceHelpBot, ready to roll dice and answer questions."
    ),
    sub_agents=[roll_agent],
    tools=[],
    generate_content_config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(  # avoid false alarm about rolling dice.
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.OFF,
            ),
        ]
    ),
)
