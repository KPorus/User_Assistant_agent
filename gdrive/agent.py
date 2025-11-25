from google.adk.agents.llm_agent import LlmAgent
from google.genai import types
from google.adk.runners import Runner
from dotenv import load_dotenv
import os
load_dotenv()
import pathlib
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.adk.sessions import InMemorySessionService
import base64
from google.auth.transport.requests import Request

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


# ============================================================
# GOOGLE OAUTH CONFIG
# ============================================================

KEYFILE_PATH = os.getcwd() + "/gdrive/credentials/oauth.keys.json"
GDRIVE_CREDENTIALS_PATH = os.getcwd() + "/gdrive/credentials/.gdrive-server-credentials.json"
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]
PORT = 8080



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

# -- Google Drive Client --
def get_drive_client():
    authenticate_and_save("drive")
    creds = Credentials.from_authorized_user_file(GDRIVE_CREDENTIALS_PATH, DRIVE_SCOPES)
    return build("drive", "v3", credentials=creds)

def list_drive_files(page_size: int = 10, cursor: str = "", query: str = "") -> dict:
    """List files in Google Drive.
    Args:
        cursor (string): Page token for pagination, which can be None.
        page_size (int): Number of files to return per page.
        query (str): Query string to filter files.
    Returns:
        dict: A dictionary containing a list of files and the next page token.
    """

    drive = get_drive_client()
    if not query:
        query = "trashed = false"
    else:
        query = f"name contains '{query}' and trashed = false"
    params = {"pageSize": page_size, "fields": "nextPageToken, files(id, name, mimeType)", "q": query}
    if cursor:
        params["pageToken"] = cursor
    resp = drive.files().list(**params).execute()
    files = resp.get("files", [])
    return {"resources": [{"uri": f"gdrive:///{f['id']}", "mimeType": f["mimeType"], "name": f["name"]} for f in files], "nextCursor": resp.get("nextPageToken")}

def read_drive_file(file_id: str):
    drive = get_drive_client()
    meta = drive.files().get(fileId=file_id, fields="mimeType").execute()
    mime = meta.get("mimeType", "")
    if mime.startswith("application/vnd.google-apps"):
        exports = {
            "application/vnd.google-apps.document": "text/markdown",
            "application/vnd.google-apps.spreadsheet": "text/csv",
            "application/vnd.google-apps.presentation": "text/plain",
            "application/vnd.google-apps.drawing": "image/png",
        }
        out_type = exports.get(mime, "text/plain")
        data = drive.files().export(fileId=file_id, mimeType=out_type).execute()
        return {"mimeType": out_type, "content": data}
    resp = drive.files().get_media(fileId=file_id).execute()
    if mime.startswith("text/") or mime == "application/json":
        text = resp.decode("utf-8")
    else:
        text = base64.b64encode(resp).decode("utf-8")    
        return {"mimeType": mime, "content": text}


# ============================================================
# AGENT DEFINITION
# ============================================================
def gdrive():
    return LlmAgent(
    model='gemini-2.0-flash',
    name='gdrive',
    instruction=(
        "You are a Google Drive Assistant. Your job is to help the user manage "
        "and read their Google Drive files using the available tools. "
        "Capabilities: "
        "1. You can list files in Google Drive. "
        "2. You can search files by name. "
        "3. You can paginate results using the cursor returned by list_drive_files. "
        "4. You can read the contents of Google Drive files via read_drive_file. "
        "5. When reading Google Docs, Sheets, Slides, or Drawings, export them to readable formats. "
        "Rules: "
        'Always use the provided tools for Google Drive operations. '
        'Never make up file names or file contents. '
        'If the user wants to read a file, they must provide a file ID or you should first list files. '
        'Pass search queries exactly as the user writes them. '
        'Keep responses clear, brief, and based only on real tool output. '
    ),

    tools=[
        list_drive_files, read_drive_file, 
    ],
)


root_agent = gdrive()

runner = Runner(
    agent=root_agent,
    app_name="gdrive",
    session_service=session_service,
)

print("gdrive agent created successfully.")
print(runner)
