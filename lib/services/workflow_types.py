"""Service layer for workflow types."""

from typing import TYPE_CHECKING, List

from pydantic import BaseModel

from lib.workflows.categories import WORKFLOW_DISPLAY_CONFIG
from lib.workflows.models import WorkflowRunType
from lib.workflows.registry import get_all_manifests

if TYPE_CHECKING:
    from lib.workflows.manifest import WorkflowManifest

# Derived map: workflow type → category slug, built once from WORKFLOW_DISPLAY_CONFIG.
_WORKFLOW_CATEGORY_MAP: dict[WorkflowRunType, str] = {
    wf_type: category.slug
    for category in WORKFLOW_DISPLAY_CONFIG
    for wf_type in category.workflows
}


class WorkflowTypeDescription(BaseModel):
    """Workflow type description for API responses."""

    type: WorkflowRunType
    name: str
    description: str
    needs_web_search: bool
    is_experimental: bool
    is_internal: bool
    category: str

    @classmethod
    def from_manifest(cls, manifest: "WorkflowManifest") -> "WorkflowTypeDescription":
        fields = {f: getattr(manifest, f) for f in cls.model_fields if f != "category"}
        fields["category"] = _WORKFLOW_CATEGORY_MAP.get(manifest.type, "internal")
        return cls(**fields)


class WorkflowCategoryOrder(BaseModel):
    """Ordered category entry: slug, label, and ordered list of workflow type slugs."""

    slug: str
    label: str
    workflows: list[WorkflowRunType]


class WorkflowTypesResponse(BaseModel):
    """Combined response: flat workflow details plus the ordered category display config."""

    workflow_types: list[WorkflowTypeDescription]
    categories: list[WorkflowCategoryOrder]


def get_all_workflow_types() -> WorkflowTypesResponse:
    """Get all workflow types and the ordered category display config.

    The listing is the same for every caller; experimental workflows are hidden
    client-side based on the user's own preference, not filtered here.
    """
    workflow_types = [
        WorkflowTypeDescription.from_manifest(manifest)
        for manifest in get_all_manifests().values()
    ]
    categories = [
        WorkflowCategoryOrder(slug=cat.slug, label=cat.label, workflows=cat.workflows)
        for cat in WORKFLOW_DISPLAY_CONFIG
    ]

    return WorkflowTypesResponse(workflow_types=workflow_types, categories=categories)
