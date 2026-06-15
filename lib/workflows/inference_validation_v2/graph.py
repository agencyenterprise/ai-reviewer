from langgraph.graph import StateGraph

from lib.workflows.context import ContextSchema
from lib.workflows.inference_validation_v2.nodes.validate_inferences import (
    validate_inferences,
)
from lib.workflows.inference_validation_v2.state import InferenceValidationV2State


def build_inference_validation_v2_graph() -> StateGraph:
    """Build the inference-validation graph: a single deep-agent node.

    `validate_inferences` runs a deep agent that spawns three independent
    sub-agent detection passes over the document and consolidates them into a
    single severity-ranked result set.
    """
    graph = StateGraph(InferenceValidationV2State, context_schema=ContextSchema)

    graph.add_node("validate_inferences", validate_inferences)
    graph.set_entry_point("validate_inferences")
    graph.set_finish_point("validate_inferences")

    return graph  # type: ignore[return-value]


if __name__ == "__main__":

    builder = build_inference_validation_v2_graph()
    graph = builder.compile()
    graph.get_graph().draw_mermaid_png(output_file_path="inference_validation_v2.png")
