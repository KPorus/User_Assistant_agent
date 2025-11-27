### Project Name: User_Assistant_Agent

### Problem Statement  
Current AI assistants are powerful at writing and reasoning, but they are completely disconnected from your real digital life.  
They can’t read your emails, search your Drive, check your calendar, upload files, create docs and share them with others. Every useful task still ends with “now you go do it manually”.  

The goal: a single, secure, always-on agent that can actually act across Gmail, Google Drive, Docs, Calendar, web search using nothing more than natural language.

### Why agents?  
A plain LLM call is stateless and tool-less → useless for real work.  
Only an agent loop (observe → plan → use tools → observe again → repeat) can securely delegate authentication, handle multi-step workflows, and produce real outcomes instead of just text.

### What I created – Overall architecture (2025 version)

![Architecture diagram](<AI MODEL-2025-11-27-130752-1.png>)
- Core model: Gemini-2.0-flash 
- Framework: Google ADK, Google Cloud Platform  
- Authentication: OAuth2 by Google cloud platform 
- One main ReAct agent that first detects which services are needed use multiagent structure 
- Five specialised sub-routers (Gmail, Drive, Docs, Calendar, Search)  
- Full tool suite (exact same as in the diagram you posted):  
  → Gmail: search threads, send, read, delete  
  → Drive: list/search  
  → Docs: create, find, update title/content, share 
  → Calendar: free-busy, create events, list, remove
  → Search Agent: Google Custom Search 
  → General LLM fallback for reasoning/summarisation  

Everything runs on a tiny Fly.io instance + Redis for memory. Total cost < $15/month even with heavy daily use.

### Demo (these all work today)
![Test 01](image.png)
<!-- 1. “Find the contract Sarah sent last week and read the content → Invoices 2025”  
   → Gemini agent → Gmail search → download PDF → upload + move → returns shareable link

2. “Schedule a 45-min call with mike@acme.com next Thursday afternoon about the budget and attach the latest forecast Doc”  
   → Checks both calendars → finds slot → creates event with Doc link attached

3. “What are hackers saying about the new Cloudflare zero-day on Twitter right now?”  
   → Calls X search → returns real-time summary of the 12 most recent relevant tweets

4. “Summarise every file in my ‘Q4 Reports’ folder that was edited this month”  
   → Lists files → reads each one → bullet-point executive summary in <15 seconds -->

### The Build – Tech stack

- Langueges: Python
- LLM: gemini-2.0-flash-exp (via Vertex AI or Google AI Studio API)  
- Agent framework: Google ADK + Google Cloud Platform  
- Google Workspace: official google-api-python-client (Gmail, Drive, Docs, Calendar)  
- Search: Google search tools  
- OAuth2 flow: Google Cloud Oauth  
- Token storage: local folder
- Memory: google adk InMemorySession


### If I had more time

1. Add long-term vector memory for “remember everything I ever told you”  
2. Voice mode with Whisper + Gemini live streaming  
3. Make Token storage more secure
4. Give access to local PC like users can read, create, delete file from local pc (Even though i had create the agent.)  
5. Multi-agent hierarchy (spawn temporary research/finance/travel agents)  
6. Give access to drive for upload, delete
7. Use more search tools like Tavily API + twitter-api-v2 + Playwright for full-page browsing when needed
8. Mobile app (React Native) with background sync


— KPorus / User_Assistant_Agent – November 2025  
(gemini-2.0-flash + Google ADK + Google Cloud Platform )