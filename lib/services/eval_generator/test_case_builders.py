"""Test case builders for different agent types."""

from typing import Dict, List, Any


class CitationTestCaseBuilder:
    """Builds test cases for citation detection."""
    
    @classmethod
    def build(
        cls,
        test_name: str,
        chunk_index: int,
        chunk_content: str,
        citations: Dict[str, Any],
        references: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build citation test case with supporting documents (bibliography)."""
        # Extract bibliography from references for citation context
        bibliography = []
        for ref in references:
            if ref.get("text"):
                bibliography.append(ref["text"])
        
        return {
            "name": f"{test_name}_citation_chunk_{chunk_index}",
            "description": f"Citation detection test for chunk {chunk_index}",
            "input": {
                "main_document": f"data/{test_name}/main_document.md",
                "bibliography": bibliography,  # Supporting documents as bibliography
                "chunk": chunk_content
            },
            "expected_output": citations
        }


class ClaimTestCaseBuilder:
    """Builds test cases for claim detection."""
    
    @classmethod
    def build(
        cls,
        test_name: str,
        chunk_index: int,
        chunk_content: str,
        claims: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build claim test case (no supporting documents needed)."""
        return {
            "name": f"{test_name}_claim_chunk_{chunk_index}",
            "description": f"Claim detection test for chunk {chunk_index}",
            "input": {
                "main_document": f"data/{test_name}/main_document.md",
                "chunk": chunk_content
            },
            "expected_output": claims
        }


class ReferenceTestCaseBuilder:
    """Builds test cases for reference extraction."""
    
    @classmethod
    def build(
        cls,
        test_name: str,
        references: List[Dict[str, Any]],
        supporting_files: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build reference extraction test case with supporting documents."""
        # Include supporting documents as they contain the references to extract
        supporting_file_paths = []
        for i, _ in enumerate(supporting_files):
            supporting_file_paths.append(f"data/{test_name}/supporting_{i+1}.md")
        
        return {
            "name": f"{test_name}_references",
            "description": "Reference extraction test",
            "input": {
                "main_document": f"data/{test_name}/main_document.md",
                "supporting_documents": supporting_file_paths  # Supporting documents are crucial
            },
            "expected_output": {
                "references": references
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
        claims: Dict[str, Any],
        substantiations: List[Dict[str, Any]],
        supporting_files: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Build substantiation test cases with supporting documents."""
        cases = []
        
        # Include supporting documents as they're needed to substantiate claims
        supporting_file_paths = []
        for i, _ in enumerate(supporting_files):
            supporting_file_paths.append(f"data/{test_name}/supporting_{i+1}.md")
        
        # Create a test case for each substantiation result
        for i, substantiation in enumerate(substantiations):
            cases.append({
                "name": f"{test_name}_substantiation_chunk_{chunk_index}_claim_{i}",
                "description": f"Claim substantiation test for chunk {chunk_index}, claim {i}",
                "input": {
                    "main_document": f"data/{test_name}/main_document.md",
                    "supporting_documents": supporting_file_paths,  # Supporting docs are essential
                    "chunk": chunk_content,
                    "claim_index": i
                },
                "expected_output": substantiation
            })
        
        return cases
