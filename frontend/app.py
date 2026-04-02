import streamlit as st

st.set_page_config(
    page_title="SmartDoc Q&A",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar navigation
st.sidebar.title("📄 SmartDoc Q&A")
st.sidebar.caption("Intermediate RAG System")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ["📂 Dashboard", "💬 Q&A Interface", "🕘 Session History"],
)

st.sidebar.markdown("---")
st.sidebar.caption("Backend: FastAPI + ChromaDB + SQLite")
st.sidebar.caption("LLM: Gemini 1.5 Flash")

if page == "📂 Dashboard":
    from pages.dashboard import render
    render()
elif page == "💬 Q&A Interface":
    from pages.qa_interface import render
    render()
elif page == "🕘 Session History":
    from pages.session_history import render
    render()
