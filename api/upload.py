from typing import List
from fastapi import UploadFile
from lib.services.file import FileDocument, create_file_document_from_path
import tempfile
import os


async def convert_uploaded_files_to_file_document(
    uploaded_files: List[UploadFile],
) -> List[FileDocument]:
    file_documents = []

    # Create temporary directory for uploaded files
    with tempfile.TemporaryDirectory() as temp_dir:
        for uploaded_file in uploaded_files:
            # Save uploaded file to temporary location
            file_path = os.path.join(temp_dir, uploaded_file.filename)
            with open(file_path, "wb") as buffer:
                content = await uploaded_file.read()
                buffer.write(content)

            # Use the existing function to create FileDocument
            file_document = await create_file_document_from_path(file_path)
            file_documents.append(file_document)

    return file_documents
