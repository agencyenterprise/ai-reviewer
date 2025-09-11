import argparse
import asyncio
import json

from lib.services.file import File

# Run with `uv run -m cli.process_document -h`

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action", type=str, choices=["markdown", "references", "chunks", "full"]
    )
    parser.add_argument("main_document_path", type=str)
    parser.add_argument(
        "-s", "--supporting-documents", type=str, action="append", default=[]
    )
    args = parser.parse_args()

    main_document_file = File(file_path=args.main_document_path)
    supporting_documents_files = [
        File(file_path=path) for path in args.supporting_documents
    ]

    if args.action == "markdown":
        print(asyncio.run(main_document_file.get_markdown()))
    elif args.action == "references":
        from lib.services.reference_processor import ReferenceProcessor

        reference_processor = ReferenceProcessor(
            main_document=main_document_file,
            supporting_documents=supporting_documents_files,
        )
        result = asyncio.run(reference_processor.process())
        print(result.model_dump_json(indent=2))

    elif args.action == "chunks":
        from lib.services.document_processor import DocumentProcessor

        processor = DocumentProcessor(main_document_file)

        chunks = asyncio.run(processor.get_chunks())

        serialized_chunks = []
        for index, chunk in enumerate(chunks):
            serialized_chunks.append(
                {
                    "index": index,
                    "page_content": chunk.page_content,
                    "metadata": chunk.metadata,
                }
            )
        print(json.dumps(serialized_chunks, ensure_ascii=False, indent=2))
    elif args.action == "full":
        from lib.agents.claim_detector import claim_detector_agent
        from lib.agents.citation_detector import citation_detector_agent
        from lib.services.document_processor import DocumentProcessor

        processor = DocumentProcessor(main_document_file)

        results = asyncio.run(
            processor.apply_agents_to_all_chunks(
                [claim_detector_agent, citation_detector_agent]
            )
        )
        print(results)
    else:
        print(f"Unknown action: {args.action}")
