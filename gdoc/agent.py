from google.adk.agents import Agent
from google.genai import types
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import os
from typing import List, Dict
import pathlib



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
# 1. Authentication
# =============================================================================

KEYFILE_PATH = os.getcwd() + "/gdoc/credentials/oauth.keys.json"
GDRIVE_CREDENTIALS_PATH = os.getcwd() + "/gdoc/credentials/.gdrive-server-credentials.json"
GDOC_CREDENTIALS_PATH = os.getcwd() + "/gdoc/credentials/.gdoc-server-credentials.json"
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]
PORT = 8080
SCOPES = [
    'https://www.googleapis.com/auth/documents',
]

def get_docs_service():
    authenticate_and_save("docs")
    creds = Credentials.from_authorized_user_file(GDOC_CREDENTIALS_PATH, SCOPES)
    return build('docs', 'v1', credentials=creds)

def get_drive_service():
    authenticate_and_save("drive")
    creds = Credentials.from_authorized_user_file(GDRIVE_CREDENTIALS_PATH, DRIVE_SCOPES)
    return build("drive", "v3", credentials=creds)

def authenticate_and_save(app: str = "drive"):
    
    if(app == "drive"):
        if os.path.exists(GDRIVE_CREDENTIALS_PATH):
            return
        creds = None
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                # Save the refreshed credentials
                    with open(GDRIVE_CREDENTIALS_PATH, "w") as f:
                        f.write(creds.to_json())
                except Exception as e:
                    print(f"Error refreshing credentials: {e}")
                creds = None
        flow = InstalledAppFlow.from_client_secrets_file(KEYFILE_PATH, DRIVE_SCOPES)
        creds = flow.run_local_server(port=PORT,    access_type='offline',
    prompt='consent')
        pathlib.Path(os.path.dirname(GDRIVE_CREDENTIALS_PATH)).mkdir(parents=True, exist_ok=True)
        with open(GDRIVE_CREDENTIALS_PATH, "w") as f:
            f.write(creds.to_json())
        print(f"Credentials saved to {GDRIVE_CREDENTIALS_PATH}")
    elif(app == "docs"):
        if os.path.exists(GDOC_CREDENTIALS_PATH):
            return
        creds = None
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                # Save the refreshed credentials
                    with open(GDOC_CREDENTIALS_PATH, "w") as f:
                        f.write(creds.to_json())
                except Exception as e:
                    print(f"Error refreshing credentials: {e}")
                creds = None
        flow = InstalledAppFlow.from_client_secrets_file(KEYFILE_PATH, SCOPES)
        creds = flow.run_local_server(port=PORT,    access_type='offline', prompt='consent')
        pathlib.Path(os.path.dirname(GDOC_CREDENTIALS_PATH)).mkdir(parents=True, exist_ok=True)
        with open(GDOC_CREDENTIALS_PATH, "w") as f:
            f.write(creds.to_json())
        print(f"Credentials saved to {GDOC_CREDENTIALS_PATH}")


# =============================================================================
# 2. Session service (per-conversation memory)
# =============================================================================
session_service = InMemorySessionService()


# def _get_cache(session_id: str) -> Dict:
#     cache = session_service.get(session_id, {})
#     if "title_to_id" not in cache:
#         cache["title_to_id"] = {}        # str → str
#         cache["last_candidates"] = []    # List[dict]
#     return cache

# =============================================================================
# 3. Tools
# =============================================================================
# def list_my_google_docs(tool_context=None, limit: int = 15) -> str:
#     """
#     List the user's most recent Google Docs by title and date.
    
#     Args:
#         tool_context: ADK-injected context (with session/state).
#         limit: Max number of docs (default: 15).
    
#     Returns:
#         Formatted list of doc titles and dates.
#     """
#     drive = get_drive_service()
#     results = drive.files().list(
#         q="mimeType='application/vnd.google-apps.document' and trashed=false",
#         orderBy="modifiedTime desc",
#         fields="files(id, name, modifiedTime)",
#         pageSize=limit
#     ).execute()
#     files = results.get('files', [])
#     if not files:
#         return "You have no Google Docs (or none accessible)."
#     lines = [f"Here are your {len(files)} most recent Google Docs:\n"]
#     for i, f in enumerate(files, 1):
#         date = f['modifiedTime'][:10]
#         lines.append(f"{i:2d}. \"{f['name']}\" — {date}")
#     lines.append("\nJust say the title (or part of it) and I'll find/open it for you!")
#     return "\n".join(lines)


def list_my_google_docs(tool_context=None, limit: int = 20) -> str:
    """
    List the user's most recent Google Docs (this version is ADK-proof).
    """
    drive = get_drive_service()
    results = drive.files().list(
        q="mimeType='application/vnd.google-apps.document' and trashed=false",
        orderBy="modifiedTime desc",
        fields="files(id, name, modifiedTime)",
        pageSize=limit
    ).execute()

    files = results.get('files', [])
    if not files:
        return "You have no Google Docs right now."

    # ADK-safe formatting – one of these two works perfectly:
    # Option 1 – Markdown code block (best visual result)
    # doc_list = "Here are your most recent Google Docs:\n\n"
    # doc_list += "```\n"
    # for i, f in enumerate(files, 1):
    #     doc_list += f"{i:2d}. \"{f['name']}\" — {f['modifiedTime'][:10]}\n"
    # doc_list += "```\n\nJust tell me the title (or number) of the one you want!"

    # Option 2 – Single-line bullets (also 100 % safe)
    doc_list = "Your recent docs: " + " | ".join(
        f"{i}. \"{f['name']}\"" for i, f in enumerate(files[:12], 1)
    ) + " — Just say the title!"

    return doc_list

def find_document_by_title(title: str, tool_context=None) -> str:
    """
    Resolve a human title → documentId with caching and disambiguation.
    
    Args:
        title: The document title to search for (exact or partial).
        tool_context: ADK-injected context.
    
    Returns:
        Document ID or message about matches/error.
    """
    session = tool_context.session if tool_context else {}
    session.setdefault("title_to_id", {})
    session.setdefault("last_candidates", [])
    clean_title = title.strip().lower()

    # Cache hit
    if clean_title in session["title_to_id"]:
        doc_id = session["title_to_id"][clean_title]
        return f"Using cached document '{title}' → ID: {doc_id}"

    drive = get_drive_service()
    # Exact match
    query = f"name = '{title}' and mimeType='application/vnd.google-apps.document' and trashed=false"
    results = drive.files().list(q=query, fields="files(id,name,modifiedTime)", pageSize=10).execute()
    files = results.get('files', [])

    # Fuzzy fallback
    if not files:
        fuzzy = f"name contains '{title}' and mimeType='application/vnd.google-apps.document' and trashed=false"
        files = drive.files().list(q=fuzzy, fields="files(id,name,modifiedTime)", pageSize=20).execute().get('files', [])

    if not files:
        return f"Error: No Google Doc found matching title '{title}'"

    files.sort(key=lambda x: x['modifiedTime'], reverse=True)

    if len(files) == 1:
        chosen = files[0]
        session["title_to_id"][clean_title] = chosen['id']
        return f"Found document: '{chosen['name']}' → ID: {chosen['id']}"

    # Multiple → disambiguate
    session["last_candidates"] = files[:10]
    lines = ["Multiple documents match:"]
    for i, f in enumerate(files[:8], 1):
        lines.append(f"{i}. '{f['name']}' (modified {f['modifiedTime'][:10]})")
    lines.append("\nReply with the number (e.g., 'use 2') or part of the exact title.")
    return "\n".join(lines)

def resolve_ambiguity(choice: str, tool_context=None) -> str:
    """
    Resolve ambiguity when multiple docs match.
    
    Args:
        choice: User's selection (e.g., "2" or "Final Report").
        tool_context: ADK-injected context.
    
    Returns:
        Confirmed document ID.
    """
    session = tool_context.session if tool_context else {}
    candidates = session.get("last_candidates", [])

    if not candidates:
        return "No previous search to clarify."

    choice_clean = choice.strip().lower()

    # Numeric choice
    if choice_clean.isdigit() or (choice_clean.startswith("use ") and choice_clean[4:].strip().isdigit()):
        idx = int("".join(filter(str.isdigit, choice_clean))) - 1
        if 0 <= idx < len(candidates):
            chosen = candidates[idx]
            session.setdefault("title_to_id", {})[chosen['name'].lower()] = chosen['id']
            session["last_candidates"] = []
            return f"Confirmed: using '{chosen['name']}' → ID: {chosen['id']}"

    # Title substring match
    for f in candidates:
        if choice_clean in f['name'].lower() or f['name'].lower() in choice_clean:
            session.setdefault("title_to_id", {})[f['name'].lower()] = f['id']
            session["last_candidates"] = []
            return f"Confirmed: using '{f['name']}' → ID: {f['id']}"

    return "I couldn't match that choice. Please reply with a number or more of the title."

def docs_operation(operation: str, document_id: str, content: str = None,
                   start_index: int = None, end_index: int = None, tool_context=None) -> str:
    """
    Read, write, or delete content in a Google Doc.
    
    Args:
        operation: 'read', 'write', or 'delete'.
        document_id: The doc ID.
        content: Text for write (optional).
        start_index/end_index: For delete/update (optional).
        tool_context: ADK-injected context.
    
    Returns:
        Result message.
    """
    service = get_docs_service()

    if operation == "read":
        doc = service.documents().get(documentId=document_id).execute()
        paragraphs = [elem for elem in doc.get('body', {}).get('content', []) if 'paragraph' in elem]
        text = ""
        for p in paragraphs:
            for elem in p.get('paragraph', {}).get('elements', []):
                tr = elem.get('textRun', {})
                if tr.get('content'):
                    text += tr['content']
        preview = text.replace('\n', ' ')[:1000]
        return f"Document content preview:\n{preview}" + ("\n..." if len(text) > 1000 else "")

    elif operation == "write" and content:
        requests = [{
            "insertText": {
                "location": {"index": start_index or 1},
                "text": content + "\n"
            }
        }]
        service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()
        return f"Successfully added text to document {document_id}"

    elif operation == "delete" and start_index is not None and end_index is not None:
        requests = [{
            "deleteContentRange": {
                "range": {"startIndex": start_index, "endIndex": end_index}
            }
        }]
        service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()
        return f"Deleted content from index {start_index} to {end_index}"

    else:
        return "Invalid operation or missing parameters."

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
- LIST all the user's recent docs anytime with list_my_google_docs and show titles and dates
- FIND any doc by title (even partial) using find_document_by_title
- READ, WRITE, or DELETE content once you know the document ID
- You are helpful and proactive

Rules:
1. If the user asks "what documents do I have?", "list my docs", "show my files", etc. → ALWAYS call list_my_google_docs first.
2. If they mention a specific title → use find_document_by_title
3. Never say "I cannot list documents" — you absolutely can!
4. After listing, encourage them: "Just tell me which one you want to work on!"
5. Always confirm before writing or deleting.
        """,
        tools=[
            list_my_google_docs,
            find_document_by_title,
            resolve_ambiguity,
            docs_operation
        ],
    )
# ────────────────────────────── RUN ──────────────────────────────
root_agent = gdocs_agent()
runner = Runner(agent=root_agent, app_name="gdoc", session_service=session_service)