from lib.services.file import FileDocument


async def format_supporting_documents_prompt_section(
    supporting_document: FileDocument, truncate_at_character_count: int = None
):
    markdown = supporting_document.markdown
    output = f"""
File name: {supporting_document.file_name}
File content converted to markdown{" (truncated)" if truncate_at_character_count else ""}:
```markdown
{markdown[:truncate_at_character_count] if truncate_at_character_count else markdown}
```
"""

    return output


async def format_supporting_documents_prompt_section_multiple(
    supporting_files: list[FileDocument],
    truncate_at_character_count: int = None,
) -> str:
    supporting_documents = "\n\n".join(
        [
            f"""### Supporting document #{index + 1} (index: {index+1})
{await format_supporting_documents_prompt_section(doc, truncate_at_character_count=truncate_at_character_count)}
"""
            for index, doc in enumerate(supporting_files or [])
        ]
    )
    return supporting_documents
