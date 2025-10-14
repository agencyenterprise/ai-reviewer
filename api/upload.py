import logging
from typing import List
from fastapi import UploadFile
from lib.services.file import FileDocument, create_file_document_from_path
import tempfile
import os
from lib.config.env import config
from xxhash import xxh128

logger = logging.getLogger(__name__)


async def convert_uploaded_files_to_file_document(
    uploaded_files: List[UploadFile],
) -> List[FileDocument]:
    file_documents = []

    upload_dir = config.FILE_UPLOADS_MOUNT_PATH

    for uploaded_file in uploaded_files:
        content = await uploaded_file.read()
        xxhash = xxh128(content).hexdigest()

        filename = uploaded_file.filename or xxhash
        file_path = os.path.join(upload_dir, xxhash)

        if os.path.exists(file_path):
            logger.info(
                f"File {filename} with hash {xxhash} already exists in {file_path}, skipping upload"
            )
        else:
            logger.info(f"Saving file {filename} with hash {xxhash} to {file_path}")
            try:
                with open(file_path, "wb") as buffer:
                    if len(content) == 0:
                        logger.warning(f"Uploaded file {filename} is empty!")

                    buffer.write(content)

                if not os.path.exists(file_path):
                    raise Exception(f"File was not created at {file_path}")

            except Exception as e:
                logger.error(f"Error processing uploaded file {filename}: {str(e)}")
                raise

        file_document = await create_file_document_from_path(
            file_path, original_file_name=filename
        )
        file_documents.append(file_document)

    return file_documents
