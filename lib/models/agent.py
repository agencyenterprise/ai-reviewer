from pyexpat import model
import uuid
from datetime import datetime
from typing import Any

from _pytest import outcomes
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import create_react_agent
from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlmodel import Boolean, JSON, Field, Float, SQLModel

from lib.models.react_agent.agent_runner import (
    _build_prompt_with_tools_preamble,
    run_agent,
    run_agent_sync,
)
from lib.models.react_agent.tool_registry import prepare_tools
from lib.models.llm import OpenAIWrapper


class Agent(SQLModel, table=True):
    __tablename__ = "agents"

    id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    )
    name: str = Field(sa_column=Column(String(255), nullable=False))
    description: str = Field(sa_column=Column(Text))
    model: str = Field(
        sa_column=Column(String(255), nullable=False)
    )  # Format: "{provider}:{model}"
    use_responses_api: bool = Field(sa_column=Column(Boolean, default=False))
    use_react_agent: bool = Field(sa_column=Column(Boolean, default=True))
    use_direct_llm_client: bool = Field(sa_column=Column(Boolean, default=False))
    use_background_mode: bool = Field(sa_column=Column(Boolean, default=False))
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
            use_responses_api=self.use_responses_api,
            timeout=300,
        )

    def _prep_llm_with_structured_output(self, llm=None):
        llm = llm or self._prep_llm()
        if self.output_schema is str:
            return llm
        else:
            return llm.with_structured_output(self.output_schema)

    def _prep_llm_with_tools(self, llm=None):
        llm = llm or self._prep_llm()
        available_tools = prepare_tools(self.tools)
        return llm.bind_tools(
            available_tools,
            tool_choice=self.mandatory_tools[0] if self.mandatory_tools else None,
        )

    def prep_llm_args(
        self,
        prompt_kwargs: dict,
        config: RunnableConfig = None,
    ):
        """Prepare arguments for normal non-react-agent llm calls"""
        if self.use_direct_llm_client:
            available_tools = prepare_tools(self.tools)
            llm_with_structure = OpenAIWrapper(
                model=self.model_name,
                background=self.use_background_mode,
                tools=available_tools,
                output_schema=self.output_schema,
            )
        else:
            # Use langchain llm
            llm = self._prep_llm()
            if (
                not self.use_react_agent
            ):  # If not using react agent, we can just add the tools to the llm itself
                llm_with_tools = self._prep_llm_with_tools(llm)
            else:
                llm_with_tools = llm
            llm_with_structure = self._prep_llm_with_structured_output(llm_with_tools)

        # Create prompt
        prompt_template = (
            self.prompt
            if hasattr(self.prompt, "format_messages")
            else ChatPromptTemplate.from_template(str(self.prompt))
        )
        messages = prompt_template.format_messages(**prompt_kwargs)

        # Apply LLM
        args = {"input": messages}
        if config is not None:
            args["config"] = config
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
        available_tool_names = [
            t.name for t in available_tools if isinstance(t, StructuredTool)
        ]
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
        llm, args = self.prep_llm_args(prompt_kwargs)
        chunk_result = await llm.ainvoke(**args)
        return chunk_result

    def _apply_sync_without_tools(
        self,
        prompt_kwargs: dict,
        config: RunnableConfig = None,
    ):
        """Apply the agent to the prompt kwargs without tools synchronously"""
        llm, args = self.prep_llm_args(prompt_kwargs)
        chunk_result = llm.invoke(**args)
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
        if len(self.tools) == 0 or not self.use_react_agent:
            return await self._apply_without_tools(prompt_kwargs, config)

        return await self._apply_with_tools(prompt_kwargs, config)

    def apply_sync(
        self,
        prompt_kwargs: dict,
        config: RunnableConfig = None,
    ):
        """Apply the agent to the prompt kwargs synchronously"""
        if len(self.tools) == 0 or not self.use_react_agent:
            return self._apply_sync_without_tools(prompt_kwargs, config)

        return self._apply_sync_with_tools(prompt_kwargs, config)
