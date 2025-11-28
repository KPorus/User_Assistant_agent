### Project Name: User_Assistant_Agent

### Problem Statement  
Most personal AI assistants (ChatGPT, Claude, Gemini, etc.) can answer questions and write emails, but they are "blind" to our real digital life. They can't read our Gmail, search our Google Drive files, check our calendar, or search google for user specific information because they have zero access to our personal data and tools.
As a result, when you ask “List down today's mail” or “Create a doc and share it with the team”, the assistant either hallucinates, gives generic advice, or tells you to do it manually.
This creates a huge gap between what an AI could do for us and what it actually does today. We want a single, trustworthy agent that can securely act across all our personal productivity tools with the same ease as a human assistant.

The goal: a single, secure, always-on agent that can actually act across Local Directory, Gmail, Google Drive, Docs, Calendar, and web search using nothing more than natural language.

### Why agents?  
Traditional “one-shot” LLMs are stateless and tool-less by design.  
Agents fix this by adding three critical capabilities:  

1. Tool use – they can call real APIs (Gmail, Drive, Calendar, web search, Google Drive, MCP, etc.)  

2. Memory & planning – they can reason step-by-step, loop, and remember context across multiple turns  

3. Secure delegated authentication – they can act on your behalf without ever seeing your passwords (using OAuth2 refresh tokens)

Only an agent architecture can safely and reliably turn natural language requests into real actions across multiple services.

### What I created – Overall architecture (2025 version)

![Architecture diagram](<AI_Architecture diagram.png>)
- Core model: Gemini-2.0-flash 
- Framework: Google ADK, Google Cloud Platform  
- Authentication: OAuth2 by Google Cloud Platform 
- One main agent that first detects which services are needed uses a multi-agent structure 
- Five specialised sub-routers (Gmail, Drive, Docs, Calendar, Search)  
- Full tool suite (same as in the diagram you posted):  
  → Gmail: search threads, send, read, delete  
  → Drive: list/search  
  → Docs: create, find, update title/content, share 
  → Calendar: free-busy, create events, list, remove
  → Search Agent: Google Custom Search 
  → MCP server fetches the user's local environment files/folders, reads, and  writes them 
  → General LLM fallback for reasoning/summarisation  


## Run locally

### Shared setup (all Google agents)

For all four agents, keep the flow and wording identical:

1) Google Cloud configuration  
- In the same GCP project, enable these APIs: Gmail API, Google Drive API, Google Docs API, and Google Calendar API.
- Under Google Auth Platform → Clients, create one OAuth 2.0 Web client (or one per agent if you prefer strict separation)
- Set Authorized JavaScript origins to:  
  - http://localhost:8000 (ADK Web UI)  
- Set Authorized redirect URIs to:  
  - http://localhost:8080/ (ADK local OAuth callback, matching your screenshot).

2) Download credentials  
- Download the client secret JSON and rename it appropriately per agent, for example:  
  - gmail/credentials/oauth.keys.json  
  - gdrive/credentialsoauth.keys.json  
  - gdoc/credentials/oauth.keys.json  
  - gcalendar/credentials/oauth.keys.json

3) Token storage convention  
- Each agent will create and reuse its own token.json in the same credentials folder, generated using google-auth-oauthlib’s InstalledAppFlow, exactly like the official Python quickstarts.

Start the agent with the built-in web UI (default http://127.0.0.1:8000):

```bash
adk web
```

For full visibility during development/debugging:

```bash
adk web --log_level DEBUG
```

Other useful local flags I use all the time:
```bash

adk web --reload --log_level DEBUG

```

That’s it — after the first `adk web`, it will automatically open the beautiful built-in ADK chat interface with Nova al-Din ready to go.

### The Build – Tech stack

- Languages: Python
- LLM: gemini-2.0-flash-exp (Google AI Studio API)  
- Agent framework: Google ADK + Google Cloud Platform  
- Google Workspace: official google-api-python-client (Gmail, Drive, Docs, Calendar)  
- Search: Google search tools  
- OAuth2 flow: Google Cloud Oauth  
- Token storage: local folder
- Memory: Google Adk InMemorySession


### If I had more time

1. Add long-term vector memory for “remember everything I ever told you.”  
2. Voice mode with Whisper + Gemini live streaming  
3. Make Token storage more secure
4. Multi-agent hierarchy (spawn temporary research/finance/travel agents)  
5. Give access to the drive for upload, delete
6. Give access to read the previous event from Google Calendar
7. Use more search tools like Tavily API + twitter-api-v2 + Playwright for full-page browsing when needed
8. Mobile app (React Native) with background sync


— KPorus / User_Assistant_Agent – November 2025  
(gemini-2.0-flash + Google ADK + Google Cloud Platform )
