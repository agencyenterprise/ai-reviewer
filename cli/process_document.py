import argparse
import asyncio
import json

from lib.services.document_processor import DocumentProcessor
from lib.services.file import File

# Run with `uv run -m cli.process_document -h`

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action", type=str, choices=["markdown", "references", "chunks", "full"]
    )
    parser.add_argument("file_path", type=str)
    args = parser.parse_args()

    file = File(file_path=args.file_path)
    processor = DocumentProcessor(file)

    if args.action == "markdown":
        print(asyncio.run(file.get_markdown()))
    elif args.action == "references":
        from lib.agents.reference_extractor import reference_extractor_agent

        full_document = asyncio.run(file.get_markdown())
        result = asyncio.run(
            reference_extractor_agent.apply(
                prompt_kwargs={
                    "full_document": full_document,
                }
            )
        )
        print(result.model_dump_json(indent=2))
    elif args.action == "chunks":
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

        results = asyncio.run(
            processor.apply_agents_to_all_chunks(
                [claim_detector_agent, citation_detector_agent]
            )
        )
        print(results)
    else:
        print(f"Unknown action: {args.action}")
