from google.adk.agents import Agent
from google.genai import types
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from gdoc.list_doc import list_my_google_docs, find_document_by_title
from gdoc.share_doc import share_google_doc, get_doc_permissions, update_doc_permission
from gdoc.doc_creation import resolve_ambiguity, docs_operation, create_google_doc
from gdoc.doc_deletion import delete_google_doc
# # ============================================================
# # GEMINI RETRY POLICY
# # ============================================================
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504]
)

# =============================================================================
# 1. Session service (per-conversation memory)
# =============================================================================
session_service = InMemorySessionService()


# =============================================================================
# Agent (Pass plain functions to tools=)
# =============================================================================
def gdocs_agent():
    return Agent(
        name="gdoc",
        model=Gemini(model="gemini-2.0-flash", retry_options=retry_config),
        instruction="""
        You are an expert Google Docs assistant.

        Core abilities:
        - LIST recent docs: list_my_google_docs
        - FIND docs by title (partial/exact): find_document_by_title (caches results)
        - CREATE new docs: create_google_doc (returns ID)
        - DELETE docs by title OR "the one you just created": find_document_by_title → delete_google_doc
        - READ/WRITE/DELETE content: docs_operation
        - SHARE docs by email: share_google_doc
        - VIEW permissions: get_doc_permissions
        - UPDATE permissions: update_doc_permission

        Smart workflows:
        1. CREATE → "Create 'Meeting Notes'" → caches ID automatically
        2. DELETE → "delete Project Plan" OR "delete the one you created" → find → confirm → delete → list updated
        3. SHARE → "share with john@company.com" → find doc → share as writer
        4. PERMISSIONS → "who has access?" → get_doc_permissions

        Examples users will say:
        - "Create project plan and share with team@company.com"
        - "List my docs" → "delete #2" → "share the new one with client"
        - "Make it public" → share_google_doc(id, None, "reader", type="anyone")
        - "Change john to reader only"

        Rules:
        1. ALWAYS confirm before DELETE (docs OR content): "Are you sure? (y/n)"
        2. Use cached IDs for "the one you just created"
        3. List docs first for vague requests ("what can I delete/share?")
        4. After delete/create/share → show list_my_google_docs
        5. For sharing: default "writer", ask role if unclear ("reader/commenter?")
        6. NEVER delete/share without explicit doc ID or cached match
        """,

        tools=[
            list_my_google_docs,
            find_document_by_title,
            resolve_ambiguity,
            docs_operation,
            create_google_doc,
            delete_google_doc,
            share_google_doc, get_doc_permissions, update_doc_permission
        ],
    )
# ────────────────────────────── RUN ──────────────────────────────
root_agent = gdocs_agent()
runner = Runner(agent=root_agent, app_name="gdoc", session_service=session_service)