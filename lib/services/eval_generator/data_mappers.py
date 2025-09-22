"""Mappers for converting analysis results to test case formats."""

from typing import Dict, Any, List


class FieldMapper:
    """Utility class for safely mapping fields from dictionaries."""
    
    @staticmethod
    def safe_get(data: Dict[str, Any], key: str, default: Any = "") -> Any:
        """Helper to safely get values from dictionaries with defaults."""
        return data.get(key, default)


class CitationMapper:
    """Mapper for citation-related data."""
    
    @classmethod
    def map_fields(cls, citation: Dict[str, Any]) -> Dict[str, Any]:
        """Map citation fields with safe defaults."""
        return {
            "text": FieldMapper.safe_get(citation, "text"),
            "type": FieldMapper.safe_get(citation, "type"),
            "format": FieldMapper.safe_get(citation, "format"),
            "needs_bibliography": FieldMapper.safe_get(citation, "needsBibliography", False),
            "associated_bibliography": FieldMapper.safe_get(citation, "associatedBibliography"),
            "index_of_associated_bibliography": FieldMapper.safe_get(citation, "indexOfAssociatedBibliography", -1),
            "rationale": FieldMapper.safe_get(citation, "rationale")
        }


class ClaimMapper:
    """Mapper for claim-related data."""
    
    @classmethod
    def map_fields(cls, claim: Dict[str, Any]) -> Dict[str, Any]:
        """Map claim fields with safe defaults."""
        return {
            "text": FieldMapper.safe_get(claim, "text"),
            "claim": FieldMapper.safe_get(claim, "claim"),
            "needs_substantiation": FieldMapper.safe_get(claim, "needsSubstantiation", False),
            "rationale": FieldMapper.safe_get(claim, "rationale")
        }


class ReferenceMapper:
    """Mapper for reference-related data."""
    
    @classmethod
    def map_fields(cls, reference: Dict[str, Any]) -> Dict[str, Any]:
        """Map reference fields with safe defaults."""
        return {
            "text": FieldMapper.safe_get(reference, "text"),
            "has_associated_supporting_document": FieldMapper.safe_get(reference, "hasAssociatedSupportingDocument", False),
            "index_of_associated_supporting_document": FieldMapper.safe_get(reference, "indexOfAssociatedSupportingDocument", -1),
            "name_of_associated_supporting_document": FieldMapper.safe_get(reference, "nameOfAssociatedSupportingDocument")
        }
