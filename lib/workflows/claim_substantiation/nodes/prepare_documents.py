from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState


async def prepare_documents(state: ClaimSubstantiatorState) -> ClaimSubstantiatorState:
    # Touch markdown for main and supporting docs to ensure they are loaded/cached
    await state["file"].get_markdown()
    for supporting_file in state.get("supporting_files", []) or []:
        await supporting_file.get_markdown()
    return {}
