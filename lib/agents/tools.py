from lib.services.file import FileDocument
from typing import Optional


def format_domain_context(domain: Optional[str]) -> str:
    """Format domain context for agent prompts."""
    if not domain:
        return ""
    
    return f"""
## Domain Context
The document is from the {domain} domain. Consider domain-specific standards, terminology, and expectations when analyzing claims. For example:
- What constitutes a significant claim may vary by domain
- Evidence requirements and citation standards may differ
- Technical terminology and concepts should be evaluated within domain context
"""


def format_audience_context(target_audience: Optional[str]) -> str:
    """Format target audience context for agent prompts."""
    if not target_audience:
        return ""
    
    return f"""
## Target Audience Context
The document is intended for: {target_audience}. Consider audience-appropriate standards when evaluating claims and evidence:
- Adjust the rigor of substantiation requirements based on audience expertise level
- Consider what level of evidence and explanation is appropriate for this audience
- Factor in audience expectations for claims, citations, and supporting evidence
"""


def format_supporting_documents_prompt_section(
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


def format_supporting_documents_prompt_section_multiple(
    supporting_files: list[FileDocument],
    truncate_at_character_count: int = None,
) -> str:
    supporting_documents = "\n\n".join(
        [
            f"""### Supporting document #{index + 1} (index: {index+1})
{format_supporting_documents_prompt_section(doc, truncate_at_character_count=truncate_at_character_count)}
"""
            for index, doc in enumerate(supporting_files or [])
        ]
    )
    return supporting_documents
