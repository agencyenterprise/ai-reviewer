"""Main eval test generator service using modular components."""

import io
import zipfile
import logging
from typing import Dict, List, Any
from fastapi.responses import StreamingResponse

from .data_mappers import FieldMapper
from .test_case_builders import (
    CitationTestCaseBuilder,
    ClaimTestCaseBuilder, 
    ReferenceTestCaseBuilder,
    SubstantiationTestCaseBuilder
)
from .file_operations import DataFileManager, YamlFileWriter, ReadmeGenerator
from .requirements_analyzer import RequirementsAnalyzer

__all__ = ["eval_test_generator"]

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
            DataFileManager.save_data_files(zip_file, results, test_name)
            citation_cases, claim_cases = self._extract_test_cases(results, test_name)
            self._write_yaml_files(zip_file, citation_cases, claim_cases, results, test_name, description)
            ReadmeGenerator.add_readme(zip_file, test_name, description)
        
        zip_buffer.seek(0)
        
        return StreamingResponse(
            io.BytesIO(zip_buffer.read()),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={test_name}_eval_package.zip"}
        )

    def generate_chunk_package(
        self, 
        results: Dict[str, Any], 
        chunk_index: int,
        selected_agents: List[str],
        test_name: str, 
        description: str
    ) -> StreamingResponse:
        """
        Generate eval test package for a specific chunk with selected agents.
        Only includes necessary files based on agent requirements.
        
        Args:
            results: Full analysis results dict with camelCase keys
            chunk_index: Index of the specific chunk to generate tests for
            selected_agents: List of agent IDs to generate tests for
            test_name: Name for the test case
            description: Description of the test case
            
        Returns:
            StreamingResponse with optimized ZIP file
        """
        logger.info(f"Generating chunk eval package '{test_name}' for chunk {chunk_index} with agents: {selected_agents}")
        
        # Get the specific chunk
        chunks = results.get("chunks", [])
        if chunk_index >= len(chunks):
            raise ValueError(f"Chunk index {chunk_index} not found in results")
        
        target_chunk = chunks[chunk_index]
        
        # Determine required files based on selected agents
        required_files = RequirementsAnalyzer.determine_required_files(selected_agents)
        
        # Create in-memory zip file
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # 1. Save only required data files
            DataFileManager.save_required_data_files(zip_file, results, test_name, required_files)
            
            # 2. Generate test cases for selected agents only
            citation_cases, claim_cases, ref_cases, substantiation_cases = self._extract_chunk_test_cases(
                target_chunk, results, selected_agents, test_name
            )
            
            # 3. Write YAML files for selected agents only
            YamlFileWriter.write_selective_yaml_files(
                zip_file, citation_cases, claim_cases, ref_cases, substantiation_cases, 
                test_name, description, selected_agents
            )
            
            # 4. Add README with optimization info
            ReadmeGenerator.add_chunk_readme(
                zip_file, test_name, description, chunk_index, selected_agents, required_files
            )
        
        zip_buffer.seek(0)
        
        return StreamingResponse(
            io.BytesIO(zip_buffer.read()),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={test_name}_chunk_{chunk_index}_eval_package.zip"}
        )

    def _extract_test_cases(self, results: Dict[str, Any], test_name: str) -> tuple[List[Dict], List[Dict]]:
        """Extract citation and claim test cases from chunks."""
        citation_cases = []
        claim_cases = []
        
        chunks = results.get("chunks", [])
        references = results.get("references", [])
        
        for chunk in chunks:
            chunk_index = FieldMapper.safe_get(chunk, "chunkIndex", 0)
            chunk_content = FieldMapper.safe_get(chunk, "content")
            citations = chunk.get("citations", {})
            claims = chunk.get("claims", {})
            
            # Process citations
            if RequirementsAnalyzer.has_valid_items(citations, "citations"):
                citation_cases.append(CitationTestCaseBuilder.build(
                    test_name, chunk_index, chunk_content, citations, references
                ))
            
            # Process claims
            if RequirementsAnalyzer.has_valid_items(claims, "claims"):
                claim_cases.append(ClaimTestCaseBuilder.build(
                    test_name, chunk_index, chunk_content, claims
                ))
        
        return citation_cases, claim_cases

    def _extract_chunk_test_cases(
        self, 
        chunk: Dict[str, Any], 
        results: Dict[str, Any], 
        selected_agents: List[str], 
        test_name: str
    ) -> tuple[List[Dict], List[Dict], List[Dict], List[Dict]]:
        """Extract test cases for a specific chunk and selected agents only."""
        chunk_index = chunk.get("chunkIndex", 0)
        chunk_content = chunk.get("content", "")
        citations = chunk.get("citations", {})
        claims = chunk.get("claims", {})
        substantiations = chunk.get("substantiations", [])
        references = results.get("references", [])
        
        citation_cases = []
        claim_cases = []
        ref_cases = []
        substantiation_cases = []
        
        # Generate cases only for selected agents
        if RequirementsAnalyzer.should_generate_agent_tests("citations", selected_agents, citations):
            citation_cases.append(CitationTestCaseBuilder.build(
                test_name, chunk_index, chunk_content, citations, references
            ))
        
        if RequirementsAnalyzer.should_generate_agent_tests("claims", selected_agents, claims):
            claim_cases.append(ClaimTestCaseBuilder.build(
                test_name, chunk_index, chunk_content, claims
            ))
        
        # Substantiation tests individual claims
        if "substantiation" in selected_agents and substantiations:
            substantiation_cases.extend(SubstantiationTestCaseBuilder.build_cases(
                test_name, chunk_index, chunk_content, claims, substantiations, results.get("supportingFiles", [])
            ))
        
        # Reference extractor works on full document, not individual chunks
        if "references" in selected_agents and references:
            supporting_files = results.get("supportingFiles", [])
            ref_cases.append(ReferenceTestCaseBuilder.build(test_name, references, supporting_files))
        
        return citation_cases, claim_cases, ref_cases, substantiation_cases

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
        YamlFileWriter.write_dataset(
            zip_file, 
            "citation_detector.yaml", 
            f"Citation Detector Dataset ({test_name})", 
            citation_cases, 
            description
        )
        
        # Write claim detector YAML
        YamlFileWriter.write_dataset(
            zip_file, 
            "claim_detector.yaml", 
            f"Claim Detector Dataset ({test_name})", 
            claim_cases, 
            description
        )
        
        # Reference extractor YAML
        references = results.get("references", [])
        supporting_files = results.get("supportingFiles", [])
        if references:
            ref_case = ReferenceTestCaseBuilder.build(test_name, references, supporting_files)
            YamlFileWriter.write_dataset(
                zip_file, 
                "reference_extractor.yaml", 
                f"Reference Extractor Dataset ({test_name})", 
                [ref_case], 
                description
            )

eval_test_generator = EvalTestGenerator()