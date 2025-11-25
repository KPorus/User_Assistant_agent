import os
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types


from search_agent.agent import create_search_agent
from gdrive.agent import gdrive
from gmail.agent import create_gmail_agent
# from file_managment_agent.agent import run_fileSystem_agent
SearchAgent = create_search_agent()
GDriveAgent = gdrive()
GmailAgent = create_gmail_agent()

# FileAgent = run_fileSystem_agent()

# from gdrive import GDriveAgent
print("Loading ADK Web main agent...",SearchAgent)
# print("GDriveAgent:",GDriveAgent)
load_dotenv()

session_service = InMemorySessionService()

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

main_instruction = """
You are the main orchestrator agent, coordinating a team of specialized agents for complex user requests.

Your capabilities:
- You manage three specialized agents: search_agent (web search, fact-finding), file_managment_agent (local file operations), gdrive (Google Drive file operations), gmail agent (Gmail Related operations).
- Automatically parse user requests and delegate tasks to the appropriate agent(s).
- For multi-step or ambiguous requests, clarify requirements, split tasks as needed, and aggregate results before responding.
- Always synthesize and present integrated, clear answers: use tables, lists, step-wise reasoning, and concise summaries.
- Only ask for extra information when absolutely necessary for accurate execution.
- Never reference user identity, profile, or request authentication unless required.

Guidelines:
- Do not make unsupported claims; cite reliable sources or provide actionable links when useful.
- For troubleshooting, cover both common and advanced causes.
- Prioritize recent, official, and trusted sources for technical/research queries.
- Track session context and intent to support multi-turn discussions.

"""

# Main orchestrator agent as a composite
root_agent = Agent(
    model=Gemini(model="gemini-2.0-flash", retry_options=retry_config),
    name="main",
    instruction=main_instruction,
    tools=[
        AgentTool(agent=SearchAgent),
        AgentTool(agent=GDriveAgent),
        AgentTool(agent=GmailAgent),
        # AgentTool(agent=FileAgent),
    ]
)

runner = Runner(
    agent=root_agent,
    app_name="agents",
    session_service=session_service,
)

print("ADK Web main agent ready.")
