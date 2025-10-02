from re import S
import uuid
from datetime import datetime
from typing import Any

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.config import RunnableConfig
from langgraph.prebuilt import create_react_agent
from sqlalchemy import JSON, Column, DateTime, Integer, String, Text, Boolean
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlmodel import JSON, Field, Float, SQLModel
from pydantic import BaseModel

from lib.config.langfuse import langfuse_handler
from lib.models.react_agent.agent_runner import (
    _build_prompt_with_tools_preamble,
    run_agent,
    run_agent_sync,
)
from lib.models.react_agent.tool_registry import prepare_tools

import logging

logger = logging.getLogger(__name__)


class QCResult(BaseModel):
    valid: bool
    feedback: str


class Agent(SQLModel, table=True):
    __tablename__ = "agents"

    id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    )
    name: str = Field(sa_column=Column(String(255), nullable=False))
    description: str = Field(sa_column=Column(Text))
    qc_prompt: Any = Field(sa_column=Column(Text, default=None))
    model: str = Field(
        sa_column=Column(String(255), nullable=False)
    )  # Format: "{provider}:{model}"
    temperature: float = Field(sa_column=Column(Float, default=0.5))
    prompt: Any = Field(sa_column=Column(Text, nullable=False))
    tools: list[str] = Field(
        sa_column=Column(ARRAY(String), default=list)
    )  # Array of tool identifiers
    mandatory_tools: list[str] = Field(
        sa_column=Column(ARRAY(String), default=list)
    )  # Array of tool identifiers
    dependencies: list[str] = Field(
        sa_column=Column(ARRAY(UUID), default=list)
    )  # Array of agent IDs
    output_schema: Any = Field(
        sa_column=Column(JSON)
    )  # JSON Schema for expected output
    version: int = Field(sa_column=Column(Integer, default=1))
    created_by: str = Field(sa_column=Column(String(255), nullable=False))  # User ID
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), default=datetime.utcnow, nullable=False
        )
    )

    # Relationships
    # chats = Relationship(back_populates="agent")

    def __repr__(self):
        return f"<Agent(id={self.id}, name='{self.name}', version={self.version})>"

    @property
    def model_provider(self):
        return str(self.model).split(":")[0]

    @property
    def model_name(self):
        return str(self.model).split(":")[1]

    def _prep_llm(self):
        return init_chat_model(
            self.model_name,
            model_provider=self.model_provider,
            temperature=self.temperature,
            timeout=300,
        )

    def _prep_llm_with_structured_output(self):
        llm = self._prep_llm()
        return llm.with_structured_output(self.output_schema)

    def prep_llm_args(self, prompt_kwargs: dict):
        """Prepare arguments for normal non-react-agent llm calls"""
        llm_with_structure = self._prep_llm_with_structured_output()

        # Create prompt
        prompt_template = (
            self.prompt
            if hasattr(self.prompt, "format_messages")
            else ChatPromptTemplate.from_template(str(self.prompt))
        )
        messages = prompt_template.format_messages(**prompt_kwargs)

        # Apply LLM
        args = {"input": messages}
        return llm_with_structure, args

    def prep_runner_args(self, prompt_kwargs: dict) -> dict:
        """Prepare common arguments for the tool-using agent runner."""
        prompt_template = (
            self.prompt
            if hasattr(self.prompt, "format_messages")
            else ChatPromptTemplate.from_template(str(self.prompt))
        )
        base_messages = prompt_template.format_messages(**prompt_kwargs)

        # Build tools
        available_tools = prepare_tools(self.tools)

        # Build messages preamble and executor
        available_tool_names = [t.name for t in available_tools]
        messages = _build_prompt_with_tools_preamble(
            base_messages, self.mandatory_tools or [], available_tool_names
        )

        llm = self._prep_llm()

        agent_executor = create_react_agent(
            llm,
            list(available_tools),
            # system_prompt,
            # checkpointer=memory or MemorySaver(), # For when we want to save chats
            # store=vector_store, # For when we want to add RAG
        )
        return {
            "executor": agent_executor,
            "messages": messages,
            "mandatory_tools": self.mandatory_tools or [],
        }

    async def _apply_without_tools(
        self,
        prompt_kwargs: dict,
        config: RunnableConfig = None,
    ):
        """Apply the agent to the prompt kwargs without tools"""
        llm_with_structure, args = self.prep_llm_args(prompt_kwargs)
        chunk_result = await llm_with_structure.ainvoke(args["input"], config=config)
        return chunk_result

    def _apply_sync_without_tools(
        self,
        prompt_kwargs: dict,
        config: RunnableConfig = None,
    ):
        """Apply the agent to the prompt kwargs without tools synchronously"""
        llm_with_structure, args = self.prep_llm_args(prompt_kwargs)
        chunk_result = llm_with_structure.invoke(args["input"], config=config)
        return chunk_result

    async def _apply_with_tools(
        self,
        prompt_kwargs: dict,
        config: RunnableConfig = None,
    ):
        """Apply the agent to the prompt kwargs with tools"""
        runner_args = self.prep_runner_args(prompt_kwargs)
        try:
            messages = await run_agent(**runner_args)
            llm_with_structure = self._prep_llm_with_structured_output()
            return llm_with_structure.invoke(
                messages
                + [
                    HumanMessage(
                        content="Now return your results in the specified structured format"
                    )
                ]
            )
        except (TypeError, ValueError, AttributeError):
            return await self._apply_without_tools(prompt_kwargs, config)

    def _apply_sync_with_tools(
        self,
        prompt_kwargs: dict,
        config: RunnableConfig = None,
    ):
        """Apply the agent to the prompt kwargs with tools synchronously"""
        runner_args = self.prep_runner_args(prompt_kwargs)
        try:
            messages = run_agent_sync(**runner_args)
            llm_with_structure = self._prep_llm_with_structured_output()
            return llm_with_structure.invoke(
                messages
                + [
                    HumanMessage(
                        content="Now return your results in the specified structured format"
                    )
                ]
            )
        except (TypeError, ValueError, AttributeError):
            return self._apply_sync_without_tools(prompt_kwargs, config)

    async def apply(
        self,
        prompt_kwargs: dict,
        config: RunnableConfig = None,
    ):
        """Apply the agent to the prompt kwargs"""

        # include empty "feedback" field in prompt_kwargs
        prompt_kwargs["feedback"] = ""

        if self.qc_prompt:
            logger.info(f"Applying agent with QC: {self.name}")
            # Try up to 3 times with QC validation
            for attempt in range(3):
                # Execute the agent
                if len(self.tools) == 0:
                    result = await self._apply_without_tools(prompt_kwargs, config)
                else:
                    result = await self._apply_with_tools(prompt_kwargs, config)

                # Run QC on the result
                prompt_template = (
                    self.prompt
                    if hasattr(self.prompt, "format_messages")
                    else ChatPromptTemplate.from_template(str(self.prompt))
                )
                agent_prompt_messages = prompt_template.format_messages(**prompt_kwargs)
                qc_result = await self._apply_run_qc(
                    result=result,
                    qc_prompt=self.qc_prompt,  # Use the dedicated QC prompt from the top of the file
                    agent_prompt=agent_prompt_messages,  # Pass formatted messages for this run
                    config=config,
                )

                # If QC passes, return the result
                if qc_result and qc_result.valid:
                    logger.info(f"QC passed for agent: {self.name}")
                    result.qc_result = qc_result
                    return result
                else:
                    logger.info(f"QC failed for agent: {self.name}")
                    logger.info(f"Providing feedback: {qc_result.feedback}")
                    prompt_kwargs["feedback"] = qc_result.feedback

                logger.info(
                    f"Attempt {attempt + 1} of 3 failed QC for agent: {self.name}"
                )

            # Set the QC result to the last result
            result.qc_result = qc_result

            # If all attempts failed QC, return the last result
            return result

        else:
            # No QC - just execute normally
            if len(self.tools) == 0:
                return await self._apply_without_tools(prompt_kwargs, config)

            return await self._apply_with_tools(prompt_kwargs, config)

    async def _apply_run_qc(self, result, qc_prompt, agent_prompt, config):
        """
        Execute quality control on another agent's result.

        Args:
            result: The result from the other agent
            qc_prompt: The QC prompt template
            agent_prompt: The original prompt that was sent to the other agent
            config: RunnableConfig for the LLM call

        Returns:
            QCResult: Structured QC result with valid flag and feedback
        """
        # Create QC prompt template
        qc_prompt_template = (
            qc_prompt
            if hasattr(qc_prompt, "format_messages")
            else ChatPromptTemplate.from_template(str(qc_prompt))
        )

        # Normalize agent prompt to string
        if isinstance(agent_prompt, str):
            agent_prompt_str = agent_prompt
        else:
            try:
                agent_prompt_str = "\n\n".join(
                    f"{m.__class__.__name__.replace('Message', '').upper()}: {getattr(m, 'content', str(m))}"
                    for m in agent_prompt
                )
            except Exception:
                agent_prompt_str = str(agent_prompt)

        # Prepare QC prompt with agent's result and original prompt
        qc_prompt_kwargs = {
            "AGENT_RESULT": str(result),
            "AGENT_PROMPT": agent_prompt_str,
        }

        # Format the QC messages
        qc_messages = qc_prompt_template.format_messages(**qc_prompt_kwargs)

        # Execute QC using a direct LLM call with structured output
        llm = self._prep_llm()
        structured_llm = llm.with_structured_output(QCResult)
        qc_result = await structured_llm.ainvoke(qc_messages, config=config)

        return qc_result

    def apply_sync(
        self,
        prompt_kwargs: dict,
        config: RunnableConfig = None,
    ):
        """Apply the agent to the prompt kwargs synchronously"""
        if len(self.tools) == 0:
            return self._apply_sync_without_tools(prompt_kwargs, config)

        return self._apply_sync_with_tools(prompt_kwargs, config)
