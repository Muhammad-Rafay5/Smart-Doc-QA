import streamlit as st
import requests
import json

API = "http://localhost:8000"


def render():
    st.title("🕘 Session History")
    st.caption("Browse all Q&A exchanges from your current session.")

    if "session_id" not in st.session_state:
        st.info("No active session found. Start a conversation in the **Q&A Interface** first.")
        return

    session_id = st.session_state.session_id
    st.info(f"**Session ID:** `{session_id}`")

    try:
        response = requests.get(
            f"{API}/chat/sessions/{session_id}/history", timeout=10
        )
        if response.status_code != 200:
            st.error("Failed to fetch session history.")
            return
        history = response.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend. Is FastAPI running on port 8000?")
        return

    if not history:
        st.info("No Q&A exchanges found for this session yet. Ask a question in the **Q&A Interface**.")
        return

    st.success(f"Found **{len(history)}** exchange(s) in this session.")
    st.markdown("---")

    for i, item in enumerate(history, 1):
        with st.expander(f"**Q{i}:** {item['question'][:80]}{'...' if len(item['question']) > 80 else ''}", expanded=(i == len(history))):
            st.markdown(f"**🕐 Time:** {item['timestamp']}")
            if item.get("namespaces_queried"):
                namespaces = item["namespaces_queried"].replace(",", ", ")
                st.markdown(f"**📁 Documents queried:** `{namespaces}`")

            st.markdown("**❓ Question:**")
            st.write(item["question"])

            st.markdown("**💡 Answer:**")
            st.write(item["answer"])

            sources = item.get("sources", [])
            if sources:
                with st.expander(f"📎 {len(sources)} Source Chunk(s)"):
                    for j, src in enumerate(sources, 1):
                        st.markdown(f"**Source {j}** — `{src['source']}`, Page {src['page']}")
                        st.text(src["text"])
                        st.markdown("---")
