import streamlit as st
import requests

API = "http://127.0.0.1:8000"


def render():
    st.title("📂 Document Dashboard")
    st.caption("Upload, manage, and monitor your indexed document library.")

    # ── Upload Section ────────────────────────────────────────────────────────
    with st.expander("📤 Upload New Document", expanded=True):
        uploaded_file = st.file_uploader(
            "Choose a PDF or TXT file",
            type=["pdf", "txt"],
            help="Only .pdf and .txt files are supported.",
        )
        if uploaded_file:
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("📥 Index Document", type="primary", use_container_width=True):
                    with st.spinner(f"Indexing '{uploaded_file.name}'..."):
                        try:
                            response = requests.post(
                                f"{API}/documents/upload-document",
                                files={
                                    "file": (
                                        uploaded_file.name,
                                        uploaded_file.getvalue(),
                                        "application/octet-stream",
                                    )
                                },
                                timeout=120,
                            )
                            if response.status_code == 200:
                                data = response.json()
                                st.success(
                                    f"✅ Indexed **{data['total_chunks']}** chunks from "
                                    f"**{uploaded_file.name}** (namespace: `{data['namespace']}`)"
                                )
                                st.rerun()
                            else:
                                detail = response.json().get("detail", "Upload failed.")
                                st.error(f"❌ {detail}")
                        except requests.exceptions.ConnectionError:
                            st.error("❌ Cannot connect to backend. Is the FastAPI server running on port 8000?")

    st.markdown("---")

    # ── Document Library ──────────────────────────────────────────────────────
    st.subheader("📚 Indexed Documents")

    try:
        response = requests.get(f"{API}/documents/", timeout=60)
        docs = response.json() if response.status_code == 200 else []
    except requests.exceptions.ConnectionError:
        st.warning("⚠️ Could not reach the backend API.")
        docs = []

    if not docs:
        st.info("No documents indexed yet. Upload a PDF or TXT file above to get started.")
        return

    # Summary metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Documents", len(docs))
    m2.metric("Total Chunks", sum(d["total_chunks"] for d in docs))
    m3.metric("Total Size", f"{sum(d['file_size_kb'] for d in docs):.1f} KB")

    st.markdown("---")

    # Document rows
    header = st.columns([3, 1, 1, 1, 1])
    header[0].markdown("**Filename**")
    header[1].markdown("**Chunks**")
    header[2].markdown("**Size (KB)**")
    header[3].markdown("**Indexed On**")
    header[4].markdown("**Action**")

    for doc in docs:
        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
        col1.write(f"📄 {doc['filename']}")
        col2.write(str(doc["total_chunks"]))
        col3.write(f"{doc['file_size_kb']:.1f}")
        col4.write(doc["created_at"][:10])

        if col5.button("🗑️ Delete", key=f"del_{doc['namespace']}"):
            try:
                r = requests.delete(
                    f"{API}/documents/{doc['namespace']}", timeout=30
                )
                if r.status_code == 200:
                    st.success(f"Deleted '{doc['filename']}'")
                    st.rerun()
                else:
                    st.error(r.json().get("detail", "Delete failed."))
            except requests.exceptions.ConnectionError:
                st.error("Cannot reach backend.")
