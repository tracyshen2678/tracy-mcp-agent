import streamlit as st
from jwt_utils import generate_token
import requests
import json

BOT_AVATAR = "🤖"
USER_AVATAR = "👤"

st.set_page_config(page_title="AI Agent Demo", page_icon="🤖")
st.title("🧑‍💼📊 Chat with your CFO")

# ------------------------
# Login Panel
# ------------------------
st.sidebar.header("User Login Simulation")
username = st.sidebar.text_input("Username", value="alice")
company_id = st.sidebar.text_input("Company ID", value="RetailGiant")

if st.sidebar.button("Login & Generate Token"):
    if username and company_id:
        try:
            token = generate_token(user_id=username, company_id=company_id)
            st.sidebar.success("✅ Login successful")
            st.session_state["token"] = token
            st.session_state["chat_history"] = []
        except Exception as e:
            st.sidebar.error(f"Token generation failed: {e}")
    else:
        st.sidebar.error("Please fill in both username and company ID")

# ------------------------
# Login Required Check
# ------------------------
if "token" not in st.session_state:
    st.warning("Please login and generate a token in the sidebar first.")
    st.stop()

token = st.session_state["token"]

# ------------------------
# Chat History State & Display
# ------------------------
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        if message.get("display_type") == "financial_monitor":
            st.markdown(message["answer"])
            display_data = message["display_data"]
            if display_data:
                chart_url = display_data.get("chart_url")
                if chart_url:
                    full_chart_url = f"http://localhost:8001{chart_url}"
                    st.image(full_chart_url, caption="Financial Health Chart")
        else:
            st.markdown(message["content"])

# ------------------------
# Chat Input Area
# ------------------------
if question := st.chat_input("Ask about your company's financials..."):
    st.session_state.chat_history.append({"role": "user", "content": question})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(question)

    with st.chat_message("assistant", avatar=BOT_AVATAR):
        with st.spinner("🤖 The AI CFO is thinking..."):
            API_URL = "http://localhost:8001/ask"
            headers = {"Content-Type": "application/json"}
            payload = {"question": question, "token": token}

            try:
                response = requests.post(API_URL, json=payload, headers=headers, timeout=120)
                if response.status_code == 200:
                    response_data = response.json()
                    final_answer = response_data.get("answer", "I encountered an issue.")
                    st.markdown(final_answer)
                    display_type = response_data.get("display_type", "default")
                    display_data = response_data.get("display_data")

                    if display_type == "financial_monitor" and display_data:
                        chart_url = display_data.get("chart_url")
                        if chart_url:
                            full_chart_url = f"http://localhost:8001{chart_url}"
                            st.image(full_chart_url, caption="Financial Health Chart")

                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": final_answer,
                        "answer": final_answer,
                        "display_type": display_type,
                        "display_data": display_data
                    })

                else:
                    error_message = f"❌ Request failed: {response.status_code} - {response.text}"
                    st.error(error_message)
                    st.session_state.chat_history.append({"role": "assistant", "content": error_message})

            except requests.exceptions.RequestException as e:
                error_message = f"❌ Connection error: {e}"
                st.error(error_message)
                st.session_state.chat_history.append({"role": "assistant", "content": error_message})
