from dotenv import load_dotenv
import random
import os
import requests
from mcp.server.fastmcp import FastMCP
from typing import List, Optional, Dict, Any
from jwt_utils import verify_token
from adapters.ytj_adapter import YTJAdapter
from adapters.NOCFO_adapter import NOCFOAdapter
from adapters.financial_monitor import FinancialMonitorAdapter



os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("http_proxy", None)

# Create server
mcp = FastMCP("Echo Server", client_session_timeout_seconds=300,)
ytj = YTJAdapter()
nocfo = NOCFOAdapter()
monitor = FinancialMonitorAdapter()


load_dotenv()


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    print(f"[debug-server] add({a}, {b})")
    return a + b


@mcp.tool()
def get_secret_word() -> str:
    print("[debug-server] get_secret_word()")
    return random.choice(["apple", "banana", "cherry"])


@mcp.tool()
def get_current_weather(city: str) -> str:
    print(f"[debug-server] get_current_weather({city})")

    endpoint = "https://wttr.in"
    response = requests.get(f"{endpoint}/{city}")
    return response.text

# ================================
# NOCFO related
# ================================

@mcp.tool()
def get_company_financials(report_type: str = "all", token: Optional[str] = None) -> dict:
    """
Retrieve detailed financial data for the authenticated user's company.

As a virtual CFO, use this tool to access comprehensive financial information including:
- Balance Sheet: Evaluate assets, liabilities, and equity positions
- Income Statement: Analyze revenue streams, expenses, and profitability
- Journal: Examine chronological transaction records
- Ledger: Review categorized financial activities by account

Focus areas should include:
1. Cost optimization opportunities and expense saving recommendations
2. Cash flow risk assessment and early warning signals
3. Working capital management optimization (inventory, receivables/payables)
4. Financial health assessment and strategic recommendations

Args:
    report_type: The financial report to retrieve.
                 Options: "balance_sheet", "income_statement", "journal", "ledger", "all"
    token: The authentication token containing user and company information

Returns:
    A dictionary containing the requested financial data
    """

    return nocfo.get_company_financials_from_token(report_type, token)


@mcp.tool()
def request_other_company_data(company_id: str, report_type: str = "all", token: Optional[str] = None) -> dict:
    """
    Private:
Request financial data for a specific company. This operation requires special permissions.

Args:
    company_id: The ID of the company to get data for
    report_type: The financial report to retrieve
    token: The authentication token containing user and company information

Returns:
    A dictionary containing the requested financial data or access denied message
    """
    return nocfo.request_company_data_with_token(company_id, report_type, token)


@mcp.tool()
def forecast_financials(company_name: str, metric: str, forecast_periods: int = 12):
    """
    Predict future trends of a company's financial metric using the Hugging Face Chronos time series model.

    This tool uses historical data (from journal or ledger entries) to generate forecasts for a specified
    financial metric using a pre-trained Chronos model such as "amazon/chronos-t5-small".

    Parameters:
    - company_name (str): The name of the company to analyze (e.g., "TechNova", "KPMG").
                         The company must exist in the financial data file (NOCFO.json).
    - metric (str): The financial metric to forecast (e.g., "cash_and_cash_equivalents", "net_income", "revenue").
                    The metric should match account names in the ledger (lowercased and underscored).
    - forecast_periods (int): Number of future time steps to forecast. Default is 12.

    Functionality:
    - Extracts historical time series for the specified metric.
    - Applies the Chronos transformer model to forecast the metric for future periods.
    - Provides 0.1 / 0.5 / 0.9 quantile forecasts (with uncertainty bounds).
    - Returns a visualized plot of the forecast in base64 PNG format.

    Returns:
    {
        "historical": List[float],      # historical values
        "forecast": List[float],        # median predicted values
        "plot_base64": str              # PNG chart of the forecast (base64-encoded)
    }

    Example use cases:
    - Forecast 6-month cash flow trends for financial planning.
    - Project future revenue based on ledger history.
    - Evaluate risk or capital needs using predictive insights.
    """
    result = nocfo.forecast_company_metric(company_name, metric, forecast_periods)

    return {
        "type": "image",
        "format": "png",
        "data": result["plot_base64"],
        "caption": f"{company_name}: Forecast of {metric}"
    }





@mcp.tool()
def monitor_financial_health(token: Optional[str] = None) -> dict:
    """
    Analyzes company financial health and returns structured data for UI rendering and LLM summarization.

    This tool provides a detailed month-by-month comparison of forecasted vs. actual financial data.

    Returns:
        A dictionary containing:
        - "summary" (str): A pre-formatted markdown summary of the data.
        - "comparison_data" (dict): The raw, structured data used for plotting, keyed by account number.
    """
    if not token:
        raise ValueError("Missing token for authorization")

    user_info = verify_token(token)


    tool_output = monitor.run_monitoring(company_id=user_info["company_id"])


    return tool_output

# ================================
# YTJ related
# ================================

@mcp.tool()
def search_companies(keyword: str, active_only: bool = True):
    """
    Public: Search companies from YTJ by keyword (e.g., company name).
    Returns a list of companies that match the given keyword.
    """
    print(f"[YTJ] Searching companies with keyword: {keyword}")
    return ytj.search_companies(keyword=keyword, active_only=active_only)
@mcp.tool()
def fetch_company_details(business_id: str):
    """
    Fetch full details of a company using its Business ID from the YTJ public database.

    Use this tool when the user asks about:
    - Company details by business ID
    - Name, address, website, contact info
    - Public company profile lookup
    """
    print(f"[YTJ] Fetching company details for: {business_id}")
    return ytj.fetch_company_details(business_id=business_id)




if __name__ == "__main__":
    print("[SERVER] Starting MCP server with SSE transport...")
    mcp.run(transport="sse")
    print("[SERVER] MCP server started successfully")