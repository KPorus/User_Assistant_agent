from google.adk.agents.llm_agent import LlmAgent
from dotenv import load_dotenv
import os
import pathlib
import asyncio
import base64
from google.genai import types
from google.adk.models.google_llm import Gemini
from email.message import EmailMessage
from email import message_from_bytes
from base64 import urlsafe_b64decode

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner


session_service = InMemorySessionService()
# ============================================================
# GEMINI RETRY POLICY
# ============================================================
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504]
)


# -----------------------------------------
# CONSTANTS
# -----------------------------------------
load_dotenv()

KEYFILE_PATH = os.getcwd() + "/gmail/credentials/oauth.keys.json"
GMAIL_CREDENTIALS_PATH = os.getcwd() + "/gmail/credentials/.gmail-server-credentials.json"

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    # "https://www.googleapis.com/auth/userinfo.email",
]

PORT = 8080


# -----------------------------------------
# AUTHENTICATION
# -----------------------------------------
def authenticate_and_save():
    """Authenticate Gmail and save credentials."""
    
    # Already authenticated?
    if os.path.exists(GMAIL_CREDENTIALS_PATH):
        return

    creds = None

    # Try refresh if creds exist
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(GMAIL_CREDENTIALS_PATH, "w") as f:
                f.write(creds.to_json())
            return
        except:
            creds = None

    # Fresh login
    flow = InstalledAppFlow.from_client_secrets_file(KEYFILE_PATH, GMAIL_SCOPES)
    creds = flow.run_local_server(port=PORT, access_type="offline", prompt="consent")

    pathlib.Path(os.path.dirname(GMAIL_CREDENTIALS_PATH)).mkdir(parents=True, exist_ok=True)

    with open(GMAIL_CREDENTIALS_PATH, "w") as f:
        f.write(creds.to_json())

    print(f"Credentials saved to {GMAIL_CREDENTIALS_PATH}")


def get_gmail_client():
    """Return a Gmail API client."""
    authenticate_and_save()
    creds = Credentials.from_authorized_user_file(GMAIL_CREDENTIALS_PATH, GMAIL_SCOPES)
    return build("gmail", "v1", credentials=creds)


# -----------------------------------------
# EMAIL ACTIONS
# -----------------------------------------

def get_current_user_email_id():
    client = get_gmail_client()
    profile = client.users().getProfile(userId="me").execute()
    print("Profile:",profile)
    return {
        "content": {
            "emailId": profile.get("emailAddress", "")
        }
    }


async def send_email(recipient_id: str, subject: str, message: str):
    """Send email using Gmail API."""
    client = get_gmail_client()
    sender_id = client.users().getProfile(userId="me").execute().get("emailAddress", "")
    print("sender ID:",sender_id)
    msg = EmailMessage()
    msg.set_content(message)
    msg["To"] = recipient_id
    msg["From"] = sender_id
    msg["Subject"] = subject

    raw_msg = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    body = {"raw": raw_msg}

    result = await asyncio.to_thread(
        client.users().messages().send(userId="me", body=body).execute
    )

    return {"status": "success", "message_id": result["id"]}


# async def fetch_metadata(client, msg_id):
#     detail = await asyncio.to_thread(
#         client.users().messages().get(
#             userId="me", 
#             id=msg_id,
#             format="metadata",
#             metadataHeaders=["Subject", "From"]
#         ).execute
#     )
#     headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
#     return {"subject": headers.get("Subject", ""), "from": headers.get("From", "")}



async def get_emails(type: str = None, max_emails=10, batch_size=5):
    """Fetch recent emails (subject, from, id) in list format."""
    client = get_gmail_client()
    query = f"in:inbox is:{type}" if type else "in:inbox"
    results = []
    next_page_token = None
    fetched = 0
    while fetched < max_emails:
        response = client.users().messages().list(
            userId="me", q=query, maxResults=batch_size,
            pageToken=next_page_token
        ).execute()
        messages = response.get("messages", [])
        for msg in messages:
            detail = client.users().messages().get(
                userId="me", id=msg["id"], format="metadata",
                metadataHeaders=["Subject", "From"]
            ).execute()
            headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
            results.append({
                "id": msg["id"],
                "subject": headers.get("Subject", ""),
                "from": headers.get("From", "")
            })
        fetched += len(messages)
        next_page_token = response.get("nextPageToken")
        if not next_page_token or fetched >= max_emails:
            break
    return results[:max_emails]

async def get_draft_mail(max_emails=10, batch_size=5):
    """Fetch recent draft emails (subject, from, id) in list format."""
    client = get_gmail_client()
    query = "in:draft"
    results = []
    next_page_token = None
    fetched = 0
    while fetched < max_emails:
        response = client.users().messages().list(
            userId="me", q=query, maxResults=batch_size,
            pageToken=next_page_token
        ).execute()
        messages = response.get("messages", [])
        for msg in messages:
            detail = client.users().messages().get(
                userId="me", id=msg["id"], format="metadata",
                metadataHeaders=["Subject", "From"]
            ).execute()
            headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
            results.append({
                "id": msg["id"],
                "subject": headers.get("Subject", ""),
                "from": headers.get("From", "")
            })
        fetched += len(messages)
        next_page_token = response.get("nextPageToken")
        if not next_page_token or fetched >= max_emails:
            break
    return results[:max_emails]


async def get_trash_mail(max_emails=10, batch_size=5):
    """Fetch recent trash emails (subject, from, id) in list format."""
    client = get_gmail_client()
    query = "in:trash"
    results = []
    next_page_token = None
    fetched = 0
    while fetched < max_emails:
        response = client.users().messages().list(
            userId="me", q=query, maxResults=batch_size,
            pageToken=next_page_token
        ).execute()
        messages = response.get("messages", [])
        for msg in messages:
            detail = client.users().messages().get(
                userId="me", id=msg["id"], format="metadata",
                metadataHeaders=["Subject", "From"]
            ).execute()
            headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
            results.append({
                "id": msg["id"],
                "subject": headers.get("Subject", ""),
                "from": headers.get("From", "")
            })
        fetched += len(messages)
        next_page_token = response.get("nextPageToken")
        if not next_page_token or fetched >= max_emails:
            break
    return results[:max_emails]


# async def get_emails(type: str = None, max_emails=50, batch_size=5):
#     """Efficiently fetch subject/from for each email via pagination. Present in list format."""
#     client = get_gmail_client()
#     if type:
#         query = f"in:inbox is:{type}"
#     else:
#         query = "in:inbox"
#     results = []
#     next_page_token = None
#     fetched = 0
#     while fetched < max_emails:
#         response = client.users().messages().list(
#             userId="me", q=query, maxResults=batch_size,
#             pageToken=next_page_token
#         ).execute()
#         messages = response.get("messages", [])
#         print("Messages batch:",messages)
#         for msg in messages:
#             detail = client.users().messages().get(
#                 userId="me", id=msg["id"], format="metadata",
#                 metadataHeaders=["Subject", "From"]
#             ).execute()
#             headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
#             results.append({"subject": headers.get("Subject", ""), "from": headers.get("From", "")})
#         # tasks = [fetch_metadata(client, msg["id"]) for msg in messages]
#         # batch_results = await asyncio.gather(*tasks)
#         # results.extend(batch_results)
#         # print(f"Fetched {len(batch_results)} emails, total so far: {len(results)}")
#         fetched += len(messages)
#         next_page_token = response.get("nextPageToken")
#         if not next_page_token or fetched >= max_emails:
#             break
#     return results[:max_emails]

# async def get_draft_mail(max_emails=50, batch_size=5):
#     """Fetch inbox email message IDs. Present subject and from address in list format.  Present in list format."""
#     client = get_gmail_client()
#     query = f"in:draft"
#     # print("Query:",query)
#     # print("Fetching emails...",client.users().messages().list(userId="me", q=query, maxResults=10).execute())
#     results = []
#     next_page_token = None
#     fetched = 0
#     while fetched < max_emails:
#         response = client.users().messages().list(
#             userId="me", q=query, maxResults=batch_size,
#             pageToken=next_page_token
#         ).execute()
#         messages = response.get("messages", [])
#         print("Messages batch:",messages)
#         for msg in messages:
#             detail = client.users().messages().get(
#                 userId="me", id=msg["id"], format="metadata",
#                 metadataHeaders=["Subject", "From"]
#             ).execute()
#             headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
#             results.append({"subject": headers.get("Subject", ""), "from": headers.get("From", "")})
#         # tasks = [fetch_metadata(client, msg["id"]) for msg in messages]
#         # batch_results = await asyncio.gather(*tasks)
#         # results.extend(batch_results)
#         # print(f"Fetched {len(batch_results)} emails, total so far: {len(results)}")
#         fetched += len(messages)
#         next_page_token = response.get("nextPageToken")
#         if not next_page_token or fetched >= max_emails:
#             break
#     return results[:max_emails]


async def read_email_content(email_id: str):
    """Read full email content."""
    client = get_gmail_client()

    msg = client.users().messages().get(userId="me", id=email_id, format="raw").execute()

    raw = urlsafe_b64decode(msg["raw"])
    mime_msg = message_from_bytes(raw)

    # Extract body
    body = None
    if mime_msg.is_multipart():
        for part in mime_msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode()
                break
    else:
        body = mime_msg.get_payload(decode=True).decode()

    return {
        "subject": mime_msg.get("subject", ""),
        "from": mime_msg.get("from", ""),
        "to": mime_msg.get("to", ""),
        "date": mime_msg.get("date", ""),
        "content": body,
    }


async def delete_email(message_id: str):
    """Move email to trash."""
    client = get_gmail_client()
    client.users().messages().trash(userId="me", id=message_id).execute()
    return "Email deleted successfully."

async def delete__trash_email(message_id: str):
    """Move email to trash."""
    client = get_gmail_client()
    client.users().messages().delete(userId="me", id=message_id).execute()
    return "Email deleted successfully."

def find_email_by_subject_or_index(email_list, subject=None, index=None):
    if subject:
        for item in email_list:
            if subject.lower() in item["subject"].lower():
                return item["id"]
    if index is not None and 0 <= index < len(email_list):
        return email_list[index]["id"]
    return None

# -----------------------------------------
# ROOT AGENT SETUP
# -----------------------------------------
def create_gmail_agent():
    return LlmAgent(
    model=Gemini(model="gemini-2.0-flash", retry_options=retry_config),
    name="gmail",
    instruction=(
        "Assist the user with Gmail operations: read, send, delete emails, "
        "and get current user info."
    ),
    tools=[
        get_current_user_email_id,
        send_email,
        get_emails,
        get_trash_mail,
        get_draft_mail,
        read_email_content,
        delete_email,
        delete__trash_email,
        find_email_by_subject_or_index,
    ],
)

root_agent = create_gmail_agent()

runner = Runner(
    agent=root_agent,
    app_name="gmail",
    session_service=session_service,
)
