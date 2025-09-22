"""Service for generating evaluation test packages from analysis results."""

import io
import zipfile
import yaml
import logging
from datetime import datetime
from typing import Dict, List, Any
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)


class EvalTestGenerator:
    """Service for generating evaluation test packages from analysis results."""

    def __init__(self):
        pass

    def generate_package(
        self, 
        results: Dict[str, Any], 
        test_name: str, 
        description: str
    ) -> StreamingResponse:
        """
        Generate complete eval test package as downloadable zip.
        
        Args:
            results: Analysis results dict with camelCase keys
            test_name: Name for the test case
            description: Description of the test case
            
        Returns:
            StreamingResponse with ZIP file
        """
        logger.info(f"Generating eval package '{test_name}' with {len(results.get('chunks', []))} chunks")
        logger.info(f"References count: {len(results.get('references', []))}")
        logger.info(f"Supporting files count: {len(results.get('supportingFiles', []))}")
        
        # Create in-memory zip file
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            
            self._save_data_files(zip_file, results, test_name)
            citation_cases, claim_cases = self._extract_test_cases(results, test_name)
            self._write_yaml_files(zip_file, citation_cases, claim_cases, results, test_name, description)
            self._add_readme(zip_file, test_name, description)
        
        zip_buffer.seek(0)
        
        return StreamingResponse(
            io.BytesIO(zip_buffer.read()),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={test_name}_eval_package.zip"}
        )

    def _save_data_files(self, zip_file: zipfile.ZipFile, results: Dict[str, Any], test_name: str):
        """Save main document and supporting files to the zip."""
        # Save main document
        main_file = results.get("file", {})
        zip_file.writestr(f"data/{test_name}/main_document.md", main_file.get("markdown", ""))
        
        # Save supporting documents
        supporting_files = results.get("supportingFiles", [])
        for i, support_doc in enumerate(supporting_files):
            zip_file.writestr(
                f"data/{test_name}/supporting_{i+1}.md", 
                support_doc.get("markdown", "")
            )

    def _extract_test_cases(self, results: Dict[str, Any], test_name: str) -> tuple[List[Dict], List[Dict]]:
        """Extract citation and claim test cases from chunks."""
        citation_cases = []
        claim_cases = []
        
        chunks = results.get("chunks", [])
        references = results.get("references", [])
        
        for chunk in chunks:
            chunk_index = chunk.get("chunkIndex", 0)
            chunk_content = chunk.get("content", "")
            citations = chunk.get("citations", {})
            claims = chunk.get("claims", {})
            
            # Process citations
            if citations and citations.get("citations"):
                citation_cases.append(self._create_citation_test_case(
                    test_name, chunk_index, chunk_content, citations, references
                ))
            
            # Process claims
            if claims and claims.get("claims"):
                claim_cases.append(self._create_claim_test_case(
                    test_name, chunk_index, chunk_content, claims
                ))
        
        return citation_cases, claim_cases

    def _create_citation_test_case(
        self, 
        test_name: str, 
        chunk_index: int, 
        chunk_content: str, 
        citations: Dict[str, Any], 
        references: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create a single citation test case."""
        return {
            "name": f"{test_name}_citation_{chunk_index}",
            "description": f"Generated citation test from chunk {chunk_index}",
            "input": {
                "main_document": f"data/{test_name}/main_document.md",
                "bibliography": [ref.get("text", "") for ref in references],
                "chunk": chunk_content
            },
            "expected_output": {
                "citations": [
                    {
                        "text": c.get("text", ""),
                        "type": c.get("type", ""),
                        "format": c.get("format", ""),
                        "needs_bibliography": c.get("needsBibliography", False),
                        "associated_bibliography": c.get("associatedBibliography", ""),
                        "index_of_associated_bibliography": c.get("indexOfAssociatedBibliography", -1),
                        "rationale": c.get("rationale", "")
                    } for c in citations.get("citations", [])
                ],
                "rationale": citations.get("rationale", "")
            }
        }

    def _create_claim_test_case(
        self, 
        test_name: str, 
        chunk_index: int, 
        chunk_content: str, 
        claims: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a single claim test case."""
        return {
            "name": f"{test_name}_claim_{chunk_index}",
            "description": f"Generated claim test from chunk {chunk_index}",
            "input": {
                "main_document": f"data/{test_name}/main_document.md",
                "chunk": chunk_content
            },
            "expected_output": {
                "claims": [
                    {
                        "text": c.get("text", ""),
                        "claim": c.get("claim", ""),
                        "needs_substantiation": c.get("needsSubstantiation", False),
                        "rationale": c.get("rationale", "")
                    } for c in claims.get("claims", [])
                ],
                "rationale": claims.get("rationale", "")
            }
        }

    def _create_reference_test_case(
        self, 
        test_name: str, 
        references: List[Dict[str, Any]], 
        supporting_files: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create reference extractor test case."""
        return {
            "name": f"{test_name}_references",
            "description": "Generated reference extraction test",
            "input": {
                "main_document": f"data/{test_name}/main_document.md",
                "supporting_documents": [
                    f"data/{test_name}/supporting_{i+1}.md" 
                    for i in range(len(supporting_files))
                ]
            },
            "expected_output": {
                "references": [
                    {
                        "text": ref.get("text", ""),
                        "has_associated_supporting_document": ref.get("hasAssociatedSupportingDocument", False),
                        "index_of_associated_supporting_document": ref.get("indexOfAssociatedSupportingDocument", -1),
                        "name_of_associated_supporting_document": ref.get("nameOfAssociatedSupportingDocument", "")
                    } for ref in references
                ]
            }
        }

    def _write_yaml_files(
        self, 
        zip_file: zipfile.ZipFile, 
        citation_cases: List[Dict], 
        claim_cases: List[Dict], 
        results: Dict[str, Any], 
        test_name: str, 
        description: str
    ):
        """Write YAML test files to the zip."""
        # Write citation detector YAML
        if citation_cases:
            citation_yaml = yaml.dump({
                "dataset": {
                    "name": f"Citation Detector Dataset ({test_name})",
                    "description": f"Generated from analysis: {description}",
                    "items": citation_cases
                }
            }, default_flow_style=False, sort_keys=False)
            zip_file.writestr("citation_detector.yaml", citation_yaml)
        
        # Write claim detector YAML
        if claim_cases:
            claim_yaml = yaml.dump({
                "dataset": {
                    "name": f"Claim Detector Dataset ({test_name})", 
                    "description": f"Generated from analysis: {description}",
                    "items": claim_cases
                }
            }, default_flow_style=False, sort_keys=False)
            zip_file.writestr("claim_detector.yaml", claim_yaml)
        
        # Reference extractor YAML
        references = results.get("references", [])
        supporting_files = results.get("supportingFiles", [])
        if references:
            ref_case = self._create_reference_test_case(test_name, references, supporting_files)
            
            ref_yaml = yaml.dump({
                "dataset": {
                    "name": f"Reference Extractor Dataset ({test_name})",
                    "description": f"Generated from analysis: {description}",
                    "items": [ref_case]
                }
            }, default_flow_style=False, sort_keys=False)
            zip_file.writestr("reference_extractor.yaml", ref_yaml)

    def _add_readme(self, zip_file: zipfile.ZipFile, test_name: str, description: str):
        """Add README with setup instructions."""
        readme_content = f"""# Generated Evaluation Test: {test_name}

## Description
{description}

## Generated Files
- `citation_detector.yaml` - Citation detection test cases
- `claim_detector.yaml` - Claim detection test cases  
- `reference_extractor.yaml` - Reference extraction test cases
- `data/{test_name}/` - Test data files

## Usage
1. Copy the YAML files to `tests/datasets/`
2. Copy the `data/` folder to `tests/`
3. Run tests with pytest

## Generated on
{datetime.now().isoformat()}
"""
        zip_file.writestr("README.md", readme_content)


eval_test_generator = EvalTestGenerator()
