import streamlit as st
from typing import List, Optional


def format_bytes(num_bytes: int) -> str:
    """Return a human-friendly file size string."""
    step_unit = 1024.0
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for unit in units:
        if size < step_unit:
            return f"{size:.2f} {unit}"
        size /= step_unit
    return f"{size:.2f} PB"


def save_uploads_to_session(
    main_document, supporting_documents: Optional[List] = None
) -> None:
    """Persist current uploads in Streamlit session state."""
    st.session_state["uploaded_main_document"] = main_document
    st.session_state["uploaded_supporting_documents"] = supporting_documents or []

    print(st.session_state["uploaded_main_document"])
    print(st.session_state["uploaded_supporting_documents"])


def render_uploaded_summary() -> None:
    """Show a compact summary of what is currently uploaded."""
    main_doc = st.session_state.get("uploaded_main_document")
    supporting_docs: List = st.session_state.get("uploaded_supporting_documents", [])

    with st.container(border=True):
        st.subheader("Current selection", anchor=False)

        if main_doc is not None:
            st.markdown("**Main document:**")
            st.write(
                {
                    "name": getattr(main_doc, "name", "(unnamed)"),
                    "type": getattr(main_doc, "type", "unknown"),
                    "size": format_bytes(getattr(main_doc, "size", 0)),
                }
            )
        else:
            st.info("No main document uploaded yet.")

        st.markdown("**Supporting documents:**")
        if supporting_docs:
            for doc in supporting_docs:
                st.write(
                    "• ",
                    getattr(doc, "name", "(unnamed)"),
                    "—",
                    format_bytes(getattr(doc, "size", 0)),
                )
        else:
            st.info("No supporting documents uploaded.")


def main() -> None:
    st.set_page_config(
        page_title="Document Uploader", page_icon="📄", layout="centered"
    )
    st.title("📄 Rand AI Reviewer")
    st.caption("Upload a single main document and any number of supporting documents.")

    # Accepted document extensions. Adjust as needed.
    allowed_types = [
        "pdf",
        "doc",
        "docx",
        "txt",
        "md",
        "rtf",
        "html",
    ]

    with st.form("document_upload_form", clear_on_submit=False):
        main_document = st.file_uploader(
            "Main document",
            type=allowed_types,
            key="main_document_input",
            help="Exactly one file that represents the primary document to be processed.",
        )

        supporting_documents = st.file_uploader(
            "Supporting documents",
            type=allowed_types,
            accept_multiple_files=True,
            key="supporting_documents_input",
            help="Zero or more files that provide additional context.",
        )

        cols = st.columns([3, 6])
        with cols[0]:
            submitted = st.form_submit_button("Process uploads", type="primary")

        if submitted:
            save_uploads_to_session(main_document, supporting_documents)

    render_uploaded_summary()


if __name__ == "__main__":
    main()
