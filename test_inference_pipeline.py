#!/usr/bin/env python3
"""
Test script for the new inference pipeline approach.

This demonstrates the two-phase approach:
1. Phase 1: Parse paragraph into statements and arguments (no tools)
2. Phase 2: Validate formalized arguments using tool calls

Run with: python test_inference_pipeline.py
"""

import asyncio
import os
from lib.agents.inference_evaluation_script import (
    run_inference_validity_pipeline,
    pretty_print_inference,
)


async def main():
    """Test the new inference pipeline approach."""

    print("API Key: ", os.environ.get("OPENAI_API_KEY"))

    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: Please set OPENAI_API_KEY environment variable")
        print("Example: export OPENAI_API_KEY='your-key-here'")
        return

    # Test paragraph
    DEMO = """If the questionnaire response rate exceeds 80%, then sampling bias is unlikely. In our pilot, the response rate exceeded 85%. Therefore, sampling bias is unlikely. Separately, since prior work shows large models generalize better, our larger model will generalize best."""

    print("=== Testing New Inference Pipeline ===")
    print(f"Input paragraph: {DEMO}")
    print()

    try:
        # Run the new two-phase pipeline
        result = await run_inference_validity_pipeline(DEMO)

        print("✅ SUCCESS: Pipeline completed without infinite loop!")
        print()

        # Display results
        pretty_print_inference(result)

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
