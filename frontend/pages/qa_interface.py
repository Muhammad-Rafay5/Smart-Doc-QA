import streamlit as st
import requests
import uuid

API = "http://localhost:8000"


def render():
    st.title("💬 Ask Your Documents")
    st.caption("Select documents and ask questions. Answers are grounded in your uploaded files.")

    # ── Session ID ─────────────────────────────────────────────────────────────
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    with st.sidebar:
        st.markdown("---")
        st.caption(f"**Session ID:**")
        st.code(st.session_state.session_id[:18] + "...", language=None)
        if st.button("🔄 New Session"):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.chat_messages = []
            st.rerun()

    # ── Document Selector ──────────────────────────────────────────────────────
    try:
        response = requests.get(f"{API}/documents/", timeout=10)
        docs = response.json() if response.status_code == 200 else []
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend. Is FastAPI running on port 8000?")
        return

    if not docs:
        st.warning("⚠️ No documents indexed yet. Go to the **Dashboard** to upload a document first.")
        return

    doc_map = {d["filename"]: d["namespace"] for d in docs}

    selected_filenames = st.multiselect(
        "📁 Select documents to query:",
        options=list(doc_map.keys()),
        help="Leave empty to query ALL indexed documents.",
        placeholder="Leave empty to query all documents...",
    )
    namespaces = [doc_map[f] for f in selected_filenames]

    if namespaces:
        st.caption(f"Querying: {', '.join(selected_filenames)}")
    else:
        st.caption("Querying: **All indexed documents**")

    st.markdown("---")

    # ── Chat History Display ───────────────────────────────────────────────────
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg["role"] == "assistant" and msg.get("sources"):
                with st.expander(f"📎 View {len(msg['sources'])} Source Chunk(s)"):
                    for i, src in enumerate(msg["sources"], 1):
                        st.markdown(
                            f"**Source {i}** — `{src['source']}`, Page {src['page']}"
                        )
                        st.text(src["text"])
                        st.markdown("---")

    # ── Question Input ─────────────────────────────────────────────────────────
    question = st.chat_input("Ask a question about your documents...")

    if question:
        # Show user message
        st.session_state.chat_messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)

        # Call API
        with st.chat_message("assistant"):
            with st.spinner("Searching and generating answer..."):
                try:
                    r = requests.post(
                        f"{API}/chat/",
                        json={
                            "question": question,
                            "session_id": st.session_state.session_id,
                            "namespaces": namespaces,
                        },
                        timeout=60,
                    )
                    if r.status_code == 200:
                        result = r.json()
                        answer = result["answer"]
                        sources = result["sources"]

                        st.write(answer)

                        if sources:
                            with st.expander(f"📎 View {len(sources)} Source Chunk(s)"):
                                for i, src in enumerate(sources, 1):
                                    st.markdown(
                                        f"**Source {i}** — `{src['source']}`, Page {src['page']}"
                                    )
                                    st.text(src["text"])
                                    st.markdown("---")

                        st.session_state.chat_messages.append(
                            {
                                "role": "assistant",
                                "content": answer,
                                "sources": sources,
                            }
                        )
                    else:
                        error_msg = r.json().get("detail", "Something went wrong.")
                        st.error(f"❌ {error_msg}")
                        st.session_state.chat_messages.append(
                            {"role": "assistant", "content": f"Error: {error_msg}"}
                        )
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to backend.")
