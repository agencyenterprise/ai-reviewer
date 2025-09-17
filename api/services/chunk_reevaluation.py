import logging
import time
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document

from lib.services.document_processor import DocumentProcessor
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState
from lib.agents.claim_detector import claim_detector_agent, ClaimResponse
from lib.agents.citation_detector import citation_detector_agent, CitationResponse
from lib.agents.claim_substantiator import claim_substantiator_agent, ClaimSubstantiationResultWithClaimIndex
from lib.services.file import FileDocument

logger = logging.getLogger(__name__)


class ChunkReevaluationService:
    """Service for re-evaluating specific document chunks with selected agents"""
    
    def __init__(self):
        self._supported_agents = {
            "claims": claim_detector_agent,
            "citations": citation_detector_agent,
            "substantiation": claim_substantiator_agent,
        }
    
    async def reevaluate_chunk(
        self,
        chunk_index: int,
        agents_to_run: List[str],
        original_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Re-evaluate a specific chunk with selected agents.
        
        Args:
            chunk_index: Zero-based index of the chunk to re-evaluate
            agents_to_run: List of agent type strings to run
            original_state: The original workflow state
            
        Returns:
            Dict containing updated results for the chunk
            
        Raises:
            ValueError: If chunk_index is invalid or agents_to_run contains unsupported agents
        """
        self._validate_inputs(chunk_index, agents_to_run, original_state)
        
        chunks = original_state.get("chunks", [])
        if chunk_index >= len(chunks):
            raise ValueError(f"Chunk index {chunk_index} is out of range (max: {len(chunks) - 1})")
        
        chunk_content = chunks[chunk_index]
        
        # Parse the file document with flexible field mapping
        file_data = original_state["file"]
        
        # Handle both camelCase and snake_case field names
        normalized_file_data = {
            "file_name": file_data.get("file_name", file_data.get("fileName", "untitled")),
            "file_path": file_data.get("file_path", file_data.get("filePath", "/tmp/temp")),
            "file_type": file_data.get("file_type", file_data.get("fileType", "text/markdown")),
            "markdown": file_data.get("markdown", "")
        }
        
        file_doc = FileDocument(**normalized_file_data)
        processor = DocumentProcessor(file=file_doc)
        
        chunk_doc = Document(page_content=chunk_content)
        
        updated_results = {}
        agents_run = []
        start_time = time.time()
        
        for agent_type in agents_to_run:
            # Skip substantiation agent for now
            if agent_type == "substantiation":
                logger.warning("Substantiation agent not supported for chunk-level re-evaluation")
                continue
                
            agent = self._supported_agents[agent_type]
            logger.info(f"Re-evaluating chunk {chunk_index} with agent: {agent_type}")
            
            # Prepare prompt kwargs based on agent requirements
            prompt_kwargs = await self._prepare_prompt_kwargs(
                agent_type, original_state, chunk_index
            )
            
            try:
                result = await processor.apply_agent_to_chunk(
                    agent=agent,
                    chunk=chunk_doc,
                    prompt_kwargs=prompt_kwargs
                )
                updated_results[agent_type] = result
                agents_run.append(agent_type)
                logger.info(f"Successfully re-evaluated chunk {chunk_index} with {agent_type}")
                
            except Exception as e:
                logger.error(f"Failed to re-evaluate chunk {chunk_index} with {agent_type}: {str(e)}")
                raise RuntimeError(f"Agent {agent_type} failed: {str(e)}")
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        return {
            "chunk_index": chunk_index,
            "chunk_content": chunk_content,
            "updated_results": updated_results,
            "agents_run": agents_run,
            "processing_time_ms": processing_time_ms
        }
    
    def _validate_inputs(
        self,
        chunk_index: int,
        agents_to_run: List[str],
        original_state: Dict[str, Any]
    ) -> None:
        """Validate input parameters"""
        if chunk_index < 0:
            raise ValueError("chunk_index must be non-negative")
        
        if not agents_to_run:
            raise ValueError("agents_to_run cannot be empty")
        
        unsupported_agents = set(agents_to_run) - set(self._supported_agents.keys())
        if unsupported_agents:
            supported_list = ", ".join(self._supported_agents.keys())
            raise ValueError(
                f"Unsupported agents: {unsupported_agents}. "
                f"Supported agents: {supported_list}"
            )
        
        if "file" not in original_state:
            raise ValueError("original_state must contain 'file'")
        
        if "chunks" not in original_state:
            raise ValueError("original_state must contain 'chunks'")
    
    async def _prepare_prompt_kwargs(
        self,
        agent_type: str,
        original_state: Dict[str, Any],
        chunk_index: int
    ) -> Dict[str, Any]:
        """Prepare additional prompt kwargs based on agent requirements"""
        prompt_kwargs = {}
        
        if agent_type == "citations":
            # Citation detector needs bibliography information
            bibliography = original_state.get("references", [])
            if bibliography:
                bibliography_text = "\n".join([
                    f"{i+1}. {ref['text'] if isinstance(ref, dict) else getattr(ref, 'text', str(ref))}" 
                    for i, ref in enumerate(bibliography)
                ])
                prompt_kwargs["bibliography"] = bibliography_text
            else:
                prompt_kwargs["bibliography"] = "No bibliography entries found."
        
        elif agent_type == "substantiation":
            # Skip substantiation for now as it requires individual claim processing
            # The substantiation agent works on individual claims, not chunk-level
            # This would require a more complex implementation to handle properly
            logger.warning(f"Substantiation agent not supported for chunk re-evaluation yet")
            return {}
        
        return prompt_kwargs
    
    def get_supported_agents(self) -> List[str]:
        """Get list of supported agent types for chunk re-evaluation"""
        # Exclude substantiation as it requires individual claim processing
        return [key for key in self._supported_agents.keys() if key != "substantiation"]