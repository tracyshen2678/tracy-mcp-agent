from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
from agents import Agent, Runner
from agents.model_settings import ModelSettings
from jwt_utils import verify_token
from agents.mcp import MCPServerSse
import asyncio
import sys
import os


sys.path.append(os.path.abspath("."))

# ================================
# Request/Response schema
# ================================
class AskRequest(BaseModel):
    question: str
    token: str

class AskResponse(BaseModel):
    answer: str

# ================================
# FastAPI app
# ================================
app = FastAPI(title="Agent API")

# ================================
# MCP server instance
# ================================
mcp_server = MCPServerSse(
    name="SSE Python Server",
    params={"url": "http://localhost:8000/sse"},
    client_session_timeout_seconds=100,
)

@app.on_event("startup")
async def startup_event():
    await mcp_server.__aenter__()

@app.on_event("shutdown")
async def shutdown_event():
    await mcp_server.__aexit__(None, None, None)

# ================================
# /ask endpoint
# ================================
@app.post("/ask", response_model=AskResponse)
async def ask_agent(req: AskRequest):
    try:
        user_info = verify_token(req.token)
        print(f"✅ Authenticated user: {user_info}")
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    agent = Agent(
        name="Assistant",

        instructions=f"""
You are a Virtual CFO assistant.

Use the tools to answer questions about the user's company and its business environment.

Security Instructions:
- For internal financial data (from NOCFO), always use the TOKEN and only access your own company's data.
- For public company information (from YTJ), you are allowed to access any company by business ID or keyword.

Tool Usage Guidelines:
- Use NOCFO tools (e.g., get_company_financials, monitor_financial_health) to retrieve internal reports and perform financial monitoring.
- For monitor_financial_health, always include the token, and do NOT analyze data from other companies.
- Use YTJ tools (e.g., fetch_company_details, search_companies) to look up public information about other companies.
- Use `fetch_company_details` to get info about a company based on business ID, including name, website, contact info, and industry.

Note:
- The `monitor_financial_health` tool returns a structured summary and comparison_data. Avoid re-summarizing using your own LLM unless the user explicitly asks for a deeper explanation or extra recommendations.
- If the user explicitly requests a more professional or strategic summary, set `use_llm=True`.

TOKEN: {req.token}
AUTHORIZED_COMPANY: {user_info["company_id"]}
""",
        mcp_servers=[mcp_server],
        model_settings=ModelSettings(tool_choice="required"),

    )

    result = await Runner.run(agent, req.question)

    return AskResponse(answer=result.final_output)

# ================================
# Run with: uvicorn agent_api:app --reload
# ================================



