"""Test case builders for different agent types."""

from typing import Dict, List, Any, Union
from pydantic import BaseModel

from lib.agents.citation_detector import CitationResponse
from lib.agents.claim_detector import ClaimResponse
from lib.agents.toulmin_claim_detector import ToulminClaimResponse
from lib.agents.reference_extractor import BibliographyItem


class CitationTestCaseBuilder:
    """Builds test cases for citation detection."""
    
    @classmethod
    def build(
        cls,
        test_name: str,
        chunk_index: int,
        chunk_content: str,
        citations: Union[CitationResponse, Dict[str, Any]],
        references: List[Union[BibliographyItem, Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Build citation test case with supporting documents (bibliography)."""
        # Extract bibliography from references for citation context
        bibliography = []
        for ref in references:
            if isinstance(ref, BaseModel):
                if hasattr(ref, 'text') and ref.text:
                    bibliography.append(ref.text)
            elif isinstance(ref, dict):
                if ref.get("text"):
                    bibliography.append(ref["text"])
        
        expected_output = citations.model_dump() if isinstance(citations, BaseModel) else citations
        
        return {
            "name": f"{test_name}_citation_chunk_{chunk_index}",
            "description": f"Citation detection test for chunk {chunk_index}",
            "input": {
                "main_document": f"data/{test_name}/main_document.md",
                "bibliography": bibliography,  # Supporting documents as bibliography
                "chunk": chunk_content
            },
            "expected_output": expected_output
        }


class ClaimTestCaseBuilder:
    """Builds test cases for claim detection."""
    
    @classmethod
    def build(
        cls,
        test_name: str,
        chunk_index: int,
        chunk_content: str,
        claims: Union[ClaimResponse, ToulminClaimResponse, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build claim test case (no supporting documents needed)."""

        expected_output = claims.model_dump() if isinstance(claims, BaseModel) else claims
        
        return {
            "name": f"{test_name}_claim_chunk_{chunk_index}",
            "description": f"Claim detection test for chunk {chunk_index}",
            "input": {
                "main_document": f"data/{test_name}/main_document.md",
                "chunk": chunk_content
            },
            "expected_output": expected_output
        }


class ReferenceTestCaseBuilder:
    """Builds test cases for reference extraction."""
    
    @classmethod
    def build(
        cls,
        test_name: str,
        references: List[Union[BibliographyItem, Dict[str, Any]]],
        supporting_files: List[Union[BaseModel, Dict[str, Any]]]  # Could be FileDocument models
    ) -> Dict[str, Any]:
        """Build reference extraction test case with supporting documents."""
        # Include supporting documents as they contain the references to extract
        supporting_file_paths = []
        for i, _ in enumerate(supporting_files):
            supporting_file_paths.append(f"data/{test_name}/supporting_{i+1}.md")

        references_output = []
        for ref in references:
            if isinstance(ref, BaseModel):
                references_output.append(ref.model_dump())
            else:
                references_output.append(ref)
        
        return {
            "name": f"{test_name}_references",
            "description": "Reference extraction test",
            "input": {
                "main_document": f"data/{test_name}/main_document.md",
                "supporting_documents": supporting_file_paths  # Supporting documents are crucial
            },
            "expected_output": {
                "references": references_output
            }
        }


class SubstantiationTestCaseBuilder:
    """Builds test cases for claim substantiation."""
    
    @classmethod
    def build_cases(
        cls,
        test_name: str,
        chunk_index: int,
        chunk_content: str,
        claims: Union[ClaimResponse, ToulminClaimResponse, Dict[str, Any]],
        substantiations: List[Union[BaseModel, Dict[str, Any]]], 
        supporting_files: List[Union[BaseModel, Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Build substantiation test cases with supporting documents."""
        cases = []
        
        # Include supporting documents as they're needed to substantiate claims
        supporting_file_paths = []
        for i, _ in enumerate(supporting_files):
            supporting_file_paths.append(f"data/{test_name}/supporting_{i+1}.md")
        
        # Create a test case for each substantiation result
        for i, substantiation in enumerate(substantiations):
            expected_output = substantiation.model_dump() if isinstance(substantiation, BaseModel) else substantiation
            
            cases.append({
                "name": f"{test_name}_substantiation_chunk_{chunk_index}_claim_{i}",
                "description": f"Claim substantiation test for chunk {chunk_index}, claim {i}",
                "input": {
                    "main_document": f"data/{test_name}/main_document.md",
                    "supporting_documents": supporting_file_paths,  # Supporting docs are essential
                    "chunk": chunk_content,
                    "claim_index": i
                },
                "expected_output": expected_output
            })
        
        return cases
