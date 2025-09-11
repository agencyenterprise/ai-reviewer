import streamlit as st
from typing import List, Optional
import asyncio
import os
from pathlib import Path
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.services.file import File
from lib.services.document_processor import DocumentProcessor
from lib.agents.claim_detector import claim_detector_agent
from lib.agents.citation_detector import citation_detector_agent
from lib.workflows.claim_substantiation import (
    run_claim_substantiator_from_paths,
)


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

    # Style primary buttons as green (used for substantiation button)
    st.markdown(
        """
        <style>
        div.stButton > button[kind="primary"] {
            background-color: #16a34a;
            border-color: #16a34a;
            color: white;
        }
        div.stButton > button[kind="primary"]:hover {
            background-color: #15803d;
            border-color: #15803d;
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

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

    def _persist_uploaded_main_document_to_path(uploaded_file) -> str:
        """Save the uploaded main document to a writable path and return path."""
        # Use persistent volume in production, fallback to local cache for development
        if os.path.exists("/app/uploads"):
            uploads_dir = Path("/app/uploads")
        else:
            uploads_dir = Path(os.getcwd()) / "cache" / "uploads"
        
        uploads_dir.mkdir(parents=True, exist_ok=True)
        target_path = uploads_dir / getattr(uploaded_file, "name", "uploaded_document")
        with open(target_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return str(target_path)

    def _persist_supporting_documents_to_paths(
        uploaded_files: Optional[List],
    ) -> List[str]:
        if not uploaded_files:
            return []
        uploads_dir = Path(os.getcwd()) / "cache" / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        paths: List[str] = []
        for uf in uploaded_files:
            target_path = uploads_dir / getattr(uf, "name", "supporting_document")
            with open(target_path, "wb") as f:
                f.write(uf.getbuffer())
            paths.append(str(target_path))
        return paths

    main_doc = st.session_state.get("uploaded_main_document")
    if main_doc is not None:
        if st.button("Run agents", type="secondary"):
            with st.spinner("Converting and analyzing document..."):
                file_path = _persist_uploaded_main_document_to_path(main_doc)
                file = File(file_path=file_path)
                processor = DocumentProcessor(file)
                try:
                    results_all = asyncio.run(
                        processor.apply_agents_to_all_chunks(
                            [claim_detector_agent, citation_detector_agent]
                        )
                    )
                except Exception as e:
                    st.error(f"Analysis failed: {e}")
                    results_all = [None, None]
                st.session_state["claim_detection_results"] = results_all[0]
                st.session_state["citation_detection_results"] = results_all[1]
                try:
                    chunks = asyncio.run(processor.get_chunks())
                    st.session_state["document_chunks"] = [
                        chunk.page_content for chunk in chunks
                    ]
                except Exception:
                    st.session_state["document_chunks"] = None

        if st.button("Run claim substantiation workflow", type="primary"):
            with st.spinner("Running substantiation workflow..."):
                file_path = _persist_uploaded_main_document_to_path(main_doc)
                supporting_uploaded = st.session_state.get(
                    "uploaded_supporting_documents", []
                )
                supporting_paths = _persist_supporting_documents_to_paths(
                    supporting_uploaded
                )
                try:
                    subst_state = asyncio.run(
                        run_claim_substantiator_from_paths(file_path, supporting_paths)
                    )
                except Exception as e:
                    st.error(f"Substantiation failed: {e}")
                    subst_state = {}
                st.session_state["claim_substantiation_results_state"] = subst_state
                # Ensure chunks are available for display
                try:
                    file = File(file_path=file_path)
                    processor = DocumentProcessor(file)
                    chunks = asyncio.run(processor.get_chunks())
                    st.session_state["document_chunks"] = [
                        chunk.page_content for chunk in chunks
                    ]
                except Exception:
                    pass

    claim_results = st.session_state.get("claim_detection_results")
    citation_results = st.session_state.get("citation_detection_results")
    chunks = st.session_state.get("document_chunks")
    if claim_results is not None or citation_results is not None:
        st.subheader("Claim detection results", anchor=False)
        for idx, item in enumerate(claim_results):
            # Prepare header indicators
            has_claims = False
            needs_subst_any = False
            data_for_header = None
            if not isinstance(item, Exception):
                try:
                    if hasattr(item, "model_dump"):
                        data_for_header = item.model_dump()
                    elif hasattr(item, "dict"):
                        data_for_header = item.dict()
                    elif isinstance(item, dict):
                        data_for_header = item
                except Exception:
                    data_for_header = None
            if isinstance(data_for_header, dict):
                claims_header = data_for_header.get("claims")
                if isinstance(claims_header, list) and len(claims_header) > 0:
                    has_claims = True
                    for _c in claims_header:
                        try:
                            if hasattr(_c, "model_dump"):
                                _c = _c.model_dump()
                            elif hasattr(_c, "dict"):
                                _c = _c.dict()
                        except Exception:
                            pass
                        try:
                            if bool(_c.get("needs_substantiation")):
                                needs_subst_any = True
                                break
                        except Exception:
                            continue

            claims_emoji = "✅" if has_claims else "❌"
            subst_emoji = "🚩" if needs_subst_any else "🟢"

            # Citation indicator for header
            has_citations = False
            try:
                if citation_results is not None and idx < len(citation_results):
                    citation_item_header = citation_results[idx]
                    if not isinstance(citation_item_header, Exception):
                        data_cit_header = None
                        try:
                            if hasattr(citation_item_header, "model_dump"):
                                data_cit_header = citation_item_header.model_dump()
                            elif hasattr(citation_item_header, "dict"):
                                data_cit_header = citation_item_header.dict()
                            elif isinstance(citation_item_header, dict):
                                data_cit_header = citation_item_header
                        except Exception:
                            data_cit_header = None
                        if isinstance(data_cit_header, dict):
                            c_list = data_cit_header.get("citations")
                            if isinstance(c_list, list) and len(c_list) > 0:
                                has_citations = True
            except Exception:
                pass

            citation_emoji = "🔗" if has_citations else ""
            header_title = (
                f"Chunk {idx + 1} {claims_emoji} {subst_emoji} {citation_emoji}"
            )

            with st.expander(header_title):
                # Show chunk text first (if available)
                if (
                    isinstance(chunks, list)
                    and idx < len(chunks)
                    and chunks[idx] is not None
                ):
                    with st.container(border=True):
                        st.markdown("**Chunk text:**")
                        st.write(chunks[idx])
                else:
                    with st.container(border=True):
                        st.info("No chunk text available.")
                if isinstance(item, Exception):
                    st.error(str(item))
                else:
                    # Try to convert Pydantic or dataclass-like objects to dicts
                    data = None
                    try:
                        if hasattr(item, "model_dump"):
                            data = item.model_dump()
                        elif hasattr(item, "dict"):
                            data = item.dict()
                        elif isinstance(item, dict):
                            data = item
                        else:
                            data = {"result": str(item)}
                    except Exception:
                        data = {"result": str(item)}

                    claims = data.get("claims") if isinstance(data, dict) else None
                    if isinstance(claims, list) and claims:
                        for c_idx, claim in enumerate(claims, start=1):
                            # Claim may be a dict or pydantic model
                            try:
                                if hasattr(claim, "model_dump"):
                                    claim = claim.model_dump()
                                elif hasattr(claim, "dict"):
                                    claim = claim.dict()
                            except Exception:
                                pass
                            with st.container(border=True):
                                needs_subst = False
                                try:
                                    needs_subst = bool(
                                        claim.get("needs_substantiation")
                                    )
                                except Exception:
                                    needs_subst = False
                                needs_emoji = "🚩" if needs_subst else "🟢"
                                st.markdown(
                                    f"**Claim {c_idx} {needs_emoji}:** {claim.get('claim', '')}"
                                )
                                st.caption(claim.get("rationale", ""))
                                st.write(
                                    {
                                        "needs_substantiation": claim.get(
                                            "needs_substantiation"
                                        )
                                    }
                                )
                    else:
                        st.info("No claims detected in this chunk.")

                    # --- Citations section ---
                    st.markdown("**Citations:**")
                    citation_item = None
                    try:
                        if citation_results is not None and idx < len(citation_results):
                            citation_item = citation_results[idx]
                    except Exception:
                        citation_item = None

                    if isinstance(citation_item, Exception):
                        st.error(str(citation_item))
                    else:
                        data_cit = None
                        try:
                            if hasattr(citation_item, "model_dump"):
                                data_cit = citation_item.model_dump()
                            elif hasattr(citation_item, "dict"):
                                data_cit = citation_item.dict()
                            elif isinstance(citation_item, dict):
                                data_cit = citation_item
                        except Exception:
                            data_cit = None

                        citations = (
                            data_cit.get("citations")
                            if isinstance(data_cit, dict)
                            else None
                        )
                        if isinstance(citations, list) and citations:
                            for t_idx, cit in enumerate(citations, start=1):
                                try:
                                    if hasattr(cit, "model_dump"):
                                        cit = cit.model_dump()
                                    elif hasattr(cit, "dict"):
                                        cit = cit.dict()
                                except Exception:
                                    pass
                                with st.container(border=True):
                                    st.markdown(
                                        f"**Citation {t_idx}:** {cit.get('text', '')}"
                                    )
                                    st.write(
                                        {
                                            "type": cit.get("type"),
                                            "format": cit.get("format"),
                                            "needs_bibliography": cit.get(
                                                "needs_bibliography"
                                            ),
                                        }
                                    )
                                    assoc = cit.get("associated_bibliography")
                                    if assoc:
                                        st.caption("Associated bibliography:")
                                        st.write(assoc)
                                    if cit.get("rationale"):
                                        st.caption(cit.get("rationale"))
                        else:
                            st.info("No citations detected in this chunk.")
                    # Also provide raw JSON for debugging/inspection
                    with st.expander("Raw claim result", expanded=False):
                        st.json(data)
                    if citation_item is not None and not isinstance(
                        citation_item, Exception
                    ):
                        with st.expander("Raw citation result", expanded=False):
                            st.json(data_cit or {})

    # --- Substantiation results section (only unsubstantiated) ---
    subst_state = st.session_state.get("claim_substantiation_results_state")
    if isinstance(subst_state, dict):
        results_by_chunk = subst_state.get("claim_substantiations_by_chunk")
        if isinstance(results_by_chunk, list) and results_by_chunk:
            st.subheader("Unsubstantiated claims by chunk", anchor=False)
            for idx, items in enumerate(results_by_chunk):
                # Normalize items to list
                if items is None:
                    continue
                unsubstantiated = []
                try:
                    for it in items:
                        if isinstance(it, Exception):
                            continue
                        data_it = None
                        try:
                            if hasattr(it, "model_dump"):
                                data_it = it.model_dump()
                            elif hasattr(it, "dict"):
                                data_it = it.dict()
                            elif isinstance(it, dict):
                                data_it = it
                        except Exception:
                            data_it = None
                        if (
                            isinstance(data_it, dict)
                            and data_it.get("is_substantiated") is False
                        ):
                            unsubstantiated.append(data_it)
                except Exception:
                    unsubstantiated = []

                if unsubstantiated:
                    with st.container(border=True):
                        st.markdown(f"**Chunk {idx + 1} — 🚩 Unsubstantiated**")
                        try:
                            if isinstance(chunks, list) and idx < len(chunks):
                                st.caption("Chunk text:")
                                st.write(chunks[idx])
                        except Exception:
                            pass
                        for u in unsubstantiated:
                            st.write(
                                {
                                    "rationale": u.get("rationale"),
                                    "feedback": u.get("feedback"),
                                }
                            )

            # Also render chunks that don't have any substantiation issues
            st.subheader("Chunks without substantiation issues", anchor=False)
            total_chunks = (
                len(chunks) if isinstance(chunks, list) else len(results_by_chunk)
            )
            for idx in range(total_chunks):
                items = results_by_chunk[idx] if idx < len(results_by_chunk) else []
                has_unsubstantiated = False
                try:
                    for it in items or []:
                        if isinstance(it, Exception):
                            continue
                        data_it = None
                        try:
                            if hasattr(it, "model_dump"):
                                data_it = it.model_dump()
                            elif hasattr(it, "dict"):
                                data_it = it.dict()
                            elif isinstance(it, dict):
                                data_it = it
                        except Exception:
                            data_it = None
                        if (
                            isinstance(data_it, dict)
                            and data_it.get("is_substantiated") is False
                        ):
                            has_unsubstantiated = True
                            break
                except Exception:
                    has_unsubstantiated = False

                if not has_unsubstantiated:
                    with st.container(border=True):
                        st.markdown(
                            f"**Chunk {idx + 1} — ✅ No substantiation issues**"
                        )
                        try:
                            if isinstance(chunks, list) and idx < len(chunks):
                                st.caption("Chunk text:")
                                st.write(chunks[idx])
                        except Exception:
                            pass


if __name__ == "__main__":
    main()
