from typing import Annotated, List, Optional
from pydantic import BaseModel, Field


class WorkflowError(BaseModel):
    """Error object for the overall workflow or specific chunks."""

    chunk_index: Optional[int] = Field(
        description="The index of the chunk that caused the error. This is None if the error occurred before the chunk was processed or in the overall workflow (not chunk-related)."
    )
    task_name: str = Field(description="The name of the task that caused the error.")
    error: str = Field(description="The error message.")
