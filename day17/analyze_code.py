#!/usr/bin/env python3
"""
Code Analysis CLI Tool
Analyzes source code files using AI-powered pipeline
"""

import sys
import os
import argparse
from pathlib import Path
from core.gemini_client import GeminiApiClient
from pipeline.pipeline_executor import CodeAnalysisPipeline


class GeminiClientWrapper:
    """Wrapper for GeminiApiClient to match expected interface"""

    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        self.client = GeminiApiClient(api_key)

    def generate_content(self, prompt: str) -> str:
        """Generate content and return text response"""
        response = self.client.generate_content(prompt)
        return self.client.extract_text(response)


def main():
    parser = argparse.ArgumentParser(
        description='Analyze source code with AI-powered pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s file.py                    # Analyze a Python file
  %(prog)s file.py -o report.txt      # Save report to file
  %(prog)s file.py -f json            # Output as JSON
  %(prog)s file.js --no-ai            # Skip AI documentation
        """
    )

    parser.add_argument(
        'file',
        help='Source code file to analyze'
    )

    parser.add_argument(
        '-o', '--output',
        help='Output file path (default: print to console)',
        default=None
    )

    parser.add_argument(
        '-f', '--format',
        choices=['txt', 'json'],
        default='txt',
        help='Output format (default: txt)'
    )

    parser.add_argument(
        '--no-ai',
        action='store_true',
        help='Skip AI documentation generation'
    )

    parser.add_argument(
        '--brief',
        action='store_true',
        help='Show brief summary only'
    )

    args = parser.parse_args()

    # Validate input file
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    if not file_path.is_file():
        print(f"Error: Not a file: {args.file}", file=sys.stderr)
        sys.exit(1)

    # Initialize Gemini client if needed
    gemini_client = None
    if not args.no_ai:
        try:
            print("Initializing AI client...")
            gemini_client = GeminiClientWrapper()
        except Exception as e:
            print(f"Warning: Could not initialize AI client: {e}", file=sys.stderr)
            print("Continuing without AI documentation...", file=sys.stderr)

    # Create pipeline
    pipeline = CodeAnalysisPipeline(gemini_client=gemini_client)

    # Analyze file
    print(f"\nAnalyzing: {args.file}")
    print("=" * 70)

    try:
        result = pipeline.analyze_file(str(file_path))
    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)
        sys.exit(1)

    # Output results
    if args.output:
        pipeline.save_result(result, args.output, format=args.format)

        # Also print brief summary to console
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Language:      {result.metadata.language}")
        print(f"Lines of code: {result.metadata.code_lines}")
        print(f"Functions:     {len(result.metadata.functions)}")
        print(f"Classes:       {len(result.metadata.classes)}")
        print(f"Quality Score: {result.quality_score:.1f}/100")
        print(f"\nFull report saved to: {args.output}")
    else:
        # Print to console
        formatted = pipeline.format_result(result, detailed=not args.brief)
        print("\n" + formatted)


if __name__ == '__main__':
    main()
