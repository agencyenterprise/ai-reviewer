"""File operations for eval package generation."""

import zipfile
import yaml
from datetime import datetime
from typing import List, Set, Dict
from .data_mappers import FieldMapper

from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState


class DataFileManager:
    """Manages data files within the eval package."""
    
    @classmethod
    def save_data_files(cls, zip_file: zipfile.ZipFile, results: ClaimSubstantiatorState, test_name: str):
        """Save main document and supporting files to the zip."""
        # Save main document
        main_file = results.file
        zip_file.writestr(
            f"data/{test_name}/main_document.md", 
            main_file.markdown if main_file else ""
        )
        
        # Save supporting documents
        supporting_files = results.supporting_files
        for i, support_doc in enumerate(supporting_files):
            zip_file.writestr(
                f"data/{test_name}/supporting_{i+1}.md", 
                support_doc.markdown
            )
    
    @classmethod
    def save_required_data_files(
        cls,
        zip_file: zipfile.ZipFile,
        results: ClaimSubstantiatorState,
        test_name: str,
        required_files: Set[str]
    ):
        """Save only the required data files based on agent needs."""
        # Always save main document
        main_file = results.file
        zip_file.writestr(
            f"data/{test_name}/main_document.md", 
            main_file.markdown if main_file else ""
        )
        
        # Only save supporting documents if needed
        if "supporting_documents" in required_files:
            supporting_files = results.supporting_files
            for i, support_doc in enumerate(supporting_files):
                zip_file.writestr(
                    f"data/{test_name}/supporting_{i+1}.md", 
                    support_doc.markdown
                )


class YamlFileWriter:
    """Handles YAML file creation and writing."""
    
    @classmethod
    def write_dataset(
        cls,
        zip_file: zipfile.ZipFile,
        filename: str,
        dataset_name: str,
        items: List[Dict],
        description: str
    ):
        """Generic method to write YAML dataset files."""
        if not items:
            return
            
        yaml_content = yaml.dump({
            "dataset": {
                "name": dataset_name,
                "description": f"Generated from analysis: {description}",
                "items": items
            }
        }, default_flow_style=False, sort_keys=False)
        
        zip_file.writestr(filename, yaml_content)
    
    @classmethod
    def write_selective_yaml_files(
        cls,
        zip_file: zipfile.ZipFile,
        citation_cases: List[Dict],
        claim_cases: List[Dict],
        ref_cases: List[Dict],
        substantiation_cases: List[Dict],
        test_name: str,
        description: str,
        selected_agents: List[str]
    ):
        """Write YAML files only for selected agents."""
        if citation_cases and "citations" in selected_agents:
            citation_yaml = yaml.dump({
                "dataset": {
                    "name": f"Citation Detector Dataset ({test_name})",
                    "description": f"Generated from chunk analysis: {description}",
                    "items": citation_cases
                }
            }, default_flow_style=False, sort_keys=False)
            zip_file.writestr("citation_detector.yaml", citation_yaml)
        
        if claim_cases and "claims" in selected_agents:
            claim_yaml = yaml.dump({
                "dataset": {
                    "name": f"Claim Detector Dataset ({test_name})", 
                    "description": f"Generated from chunk analysis: {description}",
                    "items": claim_cases
                }
            }, default_flow_style=False, sort_keys=False)
            zip_file.writestr("claim_detector.yaml", claim_yaml)
        
        if substantiation_cases and "substantiation" in selected_agents:
            substantiation_yaml = yaml.dump({
                "dataset": {
                    "name": f"Claim Substantiator Dataset ({test_name})",
                    "description": f"Generated from chunk analysis: {description}",
                    "items": substantiation_cases
                }
            }, default_flow_style=False, sort_keys=False)
            zip_file.writestr("claim_substantiator.yaml", substantiation_yaml)
        
        if ref_cases and "references" in selected_agents:
            ref_yaml = yaml.dump({
                "dataset": {
                    "name": f"Reference Extractor Dataset ({test_name})",
                    "description": f"Generated from analysis: {description}",
                    "items": ref_cases
                }
            }, default_flow_style=False, sort_keys=False)
            zip_file.writestr("reference_extractor.yaml", ref_yaml)


class ReadmeGenerator:
    """Generates README files for eval packages."""
    
    @classmethod
    def add_readme(cls, zip_file: zipfile.ZipFile, test_name: str, description: str):
        """Add README with setup instructions."""
        readme_content = f"""# Generated Evaluation Test: {test_name}

## Description
{description}

## Generated Files
- `citation_detector.yaml` - Citation detection test cases
- `claim_detector.yaml` - Claim detection test cases
- `claim_substantiator.yaml` - Claim substantiation test cases
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
    
    @classmethod
    def add_chunk_readme(
        cls,
        zip_file: zipfile.ZipFile,
        test_name: str,
        description: str,
        chunk_index: int,
        selected_agents: List[str],
        required_files: Set[str]
    ):
        """Add README with chunk-specific information."""
        agents_list = ", ".join(selected_agents)
        yaml_files = []
        
        for agent in selected_agents:
            if agent == "substantiation":
                yaml_files.append("`claim_substantiator.yaml`")
            elif agent == "claims":
                yaml_files.append("`claim_detector.yaml`")
            elif agent == "citations":
                yaml_files.append("`citation_detector.yaml`")
            elif agent == "references":
                yaml_files.append("`reference_extractor.yaml`")
        
        files_list = ", ".join(yaml_files)
        
        readme_content = f"""# Generated Chunk Evaluation Test: {test_name}

## Description
{description}

## Source
Generated from chunk {chunk_index} analysis results

## Agents Tested
{agents_list}

## Generated Files
{files_list}
- `data/{test_name}/` - Test data files

## Files Included
- Main document: ✅ Always included
- Supporting documents: {'✅ Included' if 'supporting_documents' in required_files else '❌ Not needed for selected agents'}

## Optimization
This package only includes files required by the selected agents:
- Claims/Citations: Only need main document
- References/Substantiation: Need main + supporting documents

## Usage
1. Copy the YAML files to `tests/datasets/`
2. Copy the `data/` folder to `tests/`
3. Run tests with pytest

## Generated on
{datetime.now().isoformat()}
"""
        zip_file.writestr("README.md", readme_content)
