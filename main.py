import asyncio
import os
import shutil
import subprocess
import time
from typing import Any

from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServer, MCPServerSse
from agents.model_settings import ModelSettings

# Load user token
USER_TOKEN = ""
if os.path.exists("user_token.txt"):
    with open("user_token.txt", "r") as f:
        USER_TOKEN = f.read().strip()
    print(f"[DEBUG] User token loaded successfully")
else:
    print(f"[DEBUG] No user token found. Please run login_and_run.py first.")

async def run(mcp_server: MCPServer):
    print(f"[DEBUG] Initializing agent with MCP Server...")
    agent = Agent(
        name="Assistant",
        instructions="""
You are a Virtual CFO assistant.

Use the tools to answer questions about the user's company and its business environment.

Security Instructions:
- For internal financial data (from NOCFO), always use the TOKEN and only access your own company's data.
- For public company information (from YTJ), you are allowed to access any company by business ID or keyword.

Tool Usage Guidelines:
- Use NOCFO tools (e.g., get_company_financials) for internal reports and financial statements.
- Use YTJ tools (e.g., fetch_company_details, search_companies, find_industry_peers) to look up public information about other companies, their industry, contact info, or competitors.
Use `fetch_company_details` to get info about a company based on business ID, including name, website, contact info, and industry.
TOKEN: {req.token}
AUTHORIZED_COMPANY: {user_info["company_id"]}
""",
        mcp_servers=[mcp_server],
        model_settings=ModelSettings(tool_choice="required"),
    )
    print(f"[DEBUG] Agent initialized successfully")

    print("💬 Enter your question (type 'exit' or 'quit' to stop):")
    while True:
        message = input("\n> ")
        if message.lower() in {"exit", "quit"}:
            print("👋 Exiting...")
            break

        print(f"\n🔁 Running: {message}")
        try:
            print(f"[DEBUG] Sending message to agent with authentication token")
            # assing the token in the message itself
            # The agent model should extract this and use it when calling tools
            formatted_message = f"""
TOKEN: {USER_TOKEN}

USER QUERY: {message}

Remember to use the token when accessing financial data and only analyze data for your authorized company.
"""
            result = await Runner.run(
                starting_agent=agent,
                input=formatted_message
            )
            print(f"\n✅ Response:\n{result.final_output}")
        except Exception as e:
            print(f"❌ Error: {e}")


async def main():
    print(f"[DEBUG] Connecting to SSE server with authentication...")
    async with MCPServerSse(
        name="SSE Python Server",
        params={
            "url": "http://localhost:8000/sse",
            "token": USER_TOKEN  # Pass token in connection params
        },
    ) as server:
        print(f"[DEBUG] Connected to SSE server successfully")
        trace_id = gen_trace_id()
        with trace(workflow_name="SSE Example", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n")
            await run(server)



if __name__ == "__main__":
    print(f"[DEBUG] Starting application...")
    asyncio.run(main())