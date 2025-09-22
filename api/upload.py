import logging
from typing import List
from fastapi import UploadFile
from lib.services.file import FileDocument, create_file_document_from_path
import tempfile
import os

logger = logging.getLogger(__name__)


async def convert_uploaded_files_to_file_document(
    uploaded_files: List[UploadFile],
) -> List[FileDocument]:
    file_documents = []

    # Create temporary directory for uploaded files
    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"Created temporary directory: {temp_dir}")
        
        for i, uploaded_file in enumerate(uploaded_files):
            # Log file info for debugging
            logger.info(f"Processing file {i}: filename={uploaded_file.filename}, content_type={uploaded_file.content_type}")
            
            # Handle case where filename is None or empty
            filename = uploaded_file.filename or f"upload_{i}"
            # Ensure filename is safe for filesystem
            filename = os.path.basename(filename) or f"upload_{i}"
            
            # Save uploaded file to temporary location
            file_path = os.path.join(temp_dir, filename)
            logger.info(f"Saving file to: {file_path}")
            
            try:
                with open(file_path, "wb") as buffer:
                    content = await uploaded_file.read()
                    logger.info(f"Read {len(content)} bytes from uploaded file")
                    
                    if len(content) == 0:
                        logger.warning(f"Uploaded file {filename} is empty!")
                    
                    buffer.write(content)
                
                # Verify file was written properly
                if not os.path.exists(file_path):
                    raise Exception(f"File was not created at {file_path}")
                
                file_size = os.path.getsize(file_path)
                logger.info(f"File written successfully: {file_path} ({file_size} bytes)")
                
                # Use the existing function to create FileDocument
                file_document = await create_file_document_from_path(file_path)
                logger.info(f"Created FileDocument: file_type={file_document.file_type}, file_name={file_document.file_name}")
                file_documents.append(file_document)
                
            except Exception as e:
                logger.error(f"Error processing uploaded file {filename}: {str(e)}")
                raise

    logger.info(f"Successfully processed {len(file_documents)} files")
    return file_documents
