from lib.workflows.reference_extraction.state import ExtractedReference


def format_bibliography(references: list[ExtractedReference]) -> str:
    """Format extracted references as a simple numbered list for the prompt."""

    if not references:
        return "No bibliography available."
    return "\n".join(f"{i + 1}. {ref.text}" for i, ref in enumerate(references))
