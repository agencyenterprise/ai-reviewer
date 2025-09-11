from lib.services.file import File


async def format_supporting_documents_prompt_section(
    supporting_document: File, truncate_at_character_count: int = None
):
    markdown = await supporting_document.get_markdown()
    output = f"""
File name: {supporting_document.file_name}
File content converted to markdown{" (truncated)" if truncate_at_character_count else ""}:
```markdown
{markdown[:truncate_at_character_count] if truncate_at_character_count else markdown}
```
"""

    return output
