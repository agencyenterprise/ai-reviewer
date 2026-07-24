"""Authors validator deep agent for the About This (GER) workflow.

Reads the full document, locates the "About the Authors" section,
and checks each author biography against four publication rules.
Returns structured issues and a markdown summary report.
"""

from typing import Optional

from deepagents import create_deep_agent
from langchain.agents.structured_output import AutoStrategy
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from lib.config.llm_models import gpt_5_4_model
from lib.models.agent import LangChainAgent
from lib.skills import load_skill_prompt
from lib.workflows.about_this_ger.state import AgentCheckResult
from lib.workflows.context import ContextSchema

# The author-bio rules live in the portable `about-this-authors` skill (the
# source of truth; deployments customise it by editing the skill file). This
# backend addendum carries the Draft-Detective specifics the skill omits: where
# the document lives and how to map findings onto the issues output contract.
_ENV_GUIDANCE = """\

---

## Environment & output

The document is available at `/main.md` — use your tools to read or search it.

Report findings following the conventions in the issues skill (`/skills/issues/SKILL.md`):
- one issue per failed rule per author (or the single "section not found" issue), with the title and severity given above;
- set `start_line`/`end_line` to the 1-indexed line range in `/main.md` of the text the issue refers to (typically the author's bio paragraph); when the section is absent, set both to `1` (never span the whole document);
- also produce an overall `report_markdown`: a heading naming the section found (or noting its absence), a sub-section per author listing PASS/FAIL for each rule, and a summary paragraph with counts (X authors, Y passed all rules, Z had issues).
"""


class AuthorsValidatorAgent(LangChainAgent):
    """Deep agent that validates author biographies in a document."""

    name = "Authors Validator"
    description = "Validate author biographies against publication rules"
    model = gpt_5_4_model
    temperature = 0.0
    reasoning = {"effort": "medium", "summary": "auto"}

    async def ainvoke(
        self,
        prompt_kwargs: dict,
        config: Optional[RunnableConfig] = None,
    ) -> AgentCheckResult:
        deep_agent = create_deep_agent(
            model=self.llm,
            context_schema=ContextSchema,
            response_format=AutoStrategy(AgentCheckResult),
        )

        result = await deep_agent.ainvoke(
            {
                "files": await self.context.file_artifacts_service.get_deepagent_backend_files(
                    roles=[],
                ),
                "messages": [
                    SystemMessage(
                        content=load_skill_prompt("about-this-authors")
                        + _ENV_GUIDANCE
                    ),
                    HumanMessage(
                        content=(
                            "Please read the document and validate every author "
                            "biography against all four rules. "
                            "Return the structured result and a markdown report."
                        )
                    ),
                ],
            },
            config={"recursion_limit": 100, **(config or {})},
        )

        return result["structured_response"]
