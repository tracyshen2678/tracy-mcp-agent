import os
import json
import base64
from dotenv import load_dotenv
from server import monitor_financial_health
from jwt_utils import generate_token
load_dotenv()

TEST_USER = "alice"
TEST_COMPANY = "RetailGiant"

def run_tool_test():
    print("🚀 Starting direct tool call test for 'monitor_financial_health'...")
    print("="*50)

    print("Step 1: Generating token...")
    try:
        token = generate_token(user_id=TEST_USER, company_id=TEST_COMPANY)
        print("✅ Token generated.")
    except Exception as e:
        print(f"❌ Token generation failed: {e}")
        return
    print("-"*50)

    print("Step 2: Calling the tool function directly...")
    tool_output = None
    try:
        tool_output = monitor_financial_health(token=token)
        print("✅ Tool function executed without errors.")
    except Exception as e:
        print(f"❌ Tool function failed with an exception: {e}")
        import traceback
        traceback.print_exc()
        return
    print("-"*50)

    print("Step 3: Analyzing the exact output from the tool...")

    if tool_output is None:
        print("❌ Tool did not return any output.")
        return

    print("\n--- RAW TOOL OUTPUT (as Python dictionary) ---")
    print(tool_output)
    print("---------------------------------------------\n")

    print("\n--- DETAILED BREAKDOWN OF THE OUTPUT ---")


    if isinstance(tool_output, dict):
        print("✅ Output type is a dictionary.")

        if "llm_summary_context" in tool_output:
            print("✅ 'llm_summary_context' key found.")
            summary_content = tool_output["llm_summary_context"]
            print("   - Type:", type(summary_content))
            print("   - First 150 chars:\n", summary_content[:150] + "...")
        else:
            print("❌ 'llm_summary_context' key is MISSING!")

        if "ui_display" in tool_output:
            print("✅ 'ui_display' key found.")
            ui_data = tool_output["ui_display"]
            if isinstance(ui_data, dict):
                print("   - 'ui_display' is a dictionary.")
                if "chart_url" in ui_data:
                    print("   ✅ 'chart_url' key found inside 'ui_display'.")
                    chart_url = ui_data["chart_url"]
                    print("      - Type:", type(chart_url))
                    print("      - Value:", chart_url)
                else:
                    print("   ❌ 'chart_url' key is MISSING inside 'ui_display'!")
            else:
                print("   ❌ 'ui_display' is NOT a dictionary!")
        else:
            print("❌ 'ui_display' key is MISSING!")

    else:
        print("❌ Output type is NOT a dictionary. It is:", type(tool_output))

    print("------------------------------------------\n")

    print("="*50)
    print("🎉 Test finished. Check the output above to see what the tool returns.")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    run_tool_test()