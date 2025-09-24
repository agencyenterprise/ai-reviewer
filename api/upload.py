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
        for i, uploaded_file in enumerate(uploaded_files):
            filename = uploaded_file.filename or f"upload_{i}"
            filename = os.path.basename(filename) or f"upload_{i}"
            
            # Save uploaded file to temporary location
            file_path = os.path.join(temp_dir, filename)
            
            try:
                with open(file_path, "wb") as buffer:
                    content = await uploaded_file.read()
                    
                    if len(content) == 0:
                        logger.warning(f"Uploaded file {filename} is empty!")
                    
                    buffer.write(content)
                
                if not os.path.exists(file_path):
                    raise Exception(f"File was not created at {file_path}")
                
                file_document = await create_file_document_from_path(file_path)
                file_documents.append(file_document)
                
            except Exception as e:
                logger.error(f"Error processing uploaded file {filename}: {str(e)}")
                raise

    return file_documents
