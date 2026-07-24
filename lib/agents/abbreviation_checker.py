"""Abbreviation checker agent using document search and read tools."""

from typing import Optional

from deepagents import create_deep_agent
from langchain.agents.structured_output import AutoStrategy
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from lib.config.llm_models import gpt_5_4_model
from lib.models.agent import LangChainAgent
from lib.skills import load_skill_prompt
from lib.workflows.abbreviation_scan_v2.state import AbbreviationCheckOutput
from lib.workflows.context import ContextSchema

# The extraction *method* lives in the portable `abbreviation-extraction` skill
# (the single source of truth). This backend-only addendum carries the
# Draft-Detective specifics the skill omits: where the document lives, the
# document-access tools, and the exact structured-output field mapping the
# downstream deterministic checks depend on.
_ENV_GUIDANCE = """\

---

## Environment & output

The document is available at `/main.md` — use the available search and read tools to read or
search it (e.g. search for headings like `^#+\\s*(Abbreviation|Acronym|Glossary)` to locate the
Abbreviations section).

Return the structured catalogue as the `abbreviations` list — one entry per occurrence — where
each entry records:
- `abbr`: the abbreviation in its singular base form (e.g. "LLM", not "LLMs");
- `inline_definition`: the inline definition accompanying this exact occurrence, or an empty
  string when none accompanies it;
- `occurrence_number`: the 1-based count of how many times this abbreviation has appeared so far
  (1 for the first occurrence);
- `line_start` / `line_end`: the 1-indexed line range in `/main.md` (same line number for a
  single-line occurrence);
- `abbreviations_section_definition`: the definition listed in the Abbreviations section, or
  `None` when the abbreviation is not listed there or no such section exists;
- `ignored`: `true` for occurrences excluded from compliance checks (headings, References /
  Bibliography, cover page, exempt classes), `false` otherwise;
- `ignored_reason`: a brief explanation when `ignored` is `true`, otherwise `None`.

Also set `abbreviations_section_found` to `true` only if you found and read a dedicated
Abbreviations (or equivalent) section, and provide a brief `reasoning` summary of your findings.
"""


class AbbreviationCheckerAgent(LangChainAgent):
    """Agentic agent that scans the full document for abbreviation compliance."""

    name = "Abbreviation Checker"
    description = (
        "Scan the full document for abbreviation inline definition and list coverage"
    )
    model = gpt_5_4_model
    temperature = 0.0
    reasoning = {"effort": "low", "summary": "auto"}

    async def ainvoke(
        self,
        prompt_kwargs: dict,
        config: Optional[RunnableConfig] = None,
    ) -> tuple[AbbreviationCheckOutput, list[BaseMessage]]:
        deep_agent = create_deep_agent(
            model=self.llm,
            context_schema=ContextSchema,
            response_format=AutoStrategy(AbbreviationCheckOutput),
        )

        result = await deep_agent.ainvoke(
            {
                "files": await self.context.file_artifacts_service.get_deepagent_backend_files(
                    roles=[]
                ),
                "messages": [
                    SystemMessage(
                        content=load_skill_prompt("abbreviation-extraction")
                        + _ENV_GUIDANCE
                    ),
                    HumanMessage(
                        content=(
                            "Please scan the entire document for abbreviations and acronyms. "
                            "For each occurrence record whether it has an inline definition and whether it "
                            "appears in the Abbreviations section. Return one entry per occurrence."
                        )
                    ),
                ],
            },
            config={"recursion_limit": 100, **(config or {})},
        )

        return result["structured_response"], result["messages"]
