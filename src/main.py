"""
Lease Digitizer - Main Entry Point

Command-line interface for processing lease documents.
Orchestrates the multi-agent pipeline for document classification,
extraction, and conflict detection.
"""

import argparse
import sys
from pathlib import Path

from src.config import get_settings


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Lease Digitizer - AI-powered lease document processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="Path to input file or directory containing lease documents",
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="./output",
        help="Path to output directory (default: ./output)",
    )
    
    parser.add_argument(
        "--format",
        type=str,
        choices=["json", "csv", "xlsx"],
        default="json",
        help="Output format (default: json)",
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )
    
    parser.add_argument(
        "--skip-conflicts",
        action="store_true",
        help="Skip conflict detection step",
    )
    
    return parser.parse_args()


def validate_input(input_path: str) -> Path:
    """
    Validate input path exists.
    
    Args:
        input_path: Path to validate
        
    Returns:
        Validated Path object
        
    Raises:
        SystemExit: If path doesn't exist
    """
    path = Path(input_path)
    if not path.exists():
        print(f"Error: Input path does not exist: {input_path}")
        sys.exit(1)
    return path


def process_documents(input_path: Path, output_path: Path, args: argparse.Namespace) -> None:
    """
    Process documents through the multi-agent pipeline.
    
    Args:
        input_path: Path to input documents
        output_path: Path to output directory
        args: Command line arguments
    """
    # TODO: Implement full processing pipeline
    # 1. Load documents
    # 2. Classify each document
    # 3. Extract data based on classification
    # 4. Detect conflicts (if not skipped)
    # 5. Generate output
    
    print(f"Processing documents from: {input_path}")
    print(f"Output will be written to: {output_path}")
    
    # Placeholder for pipeline implementation
    raise NotImplementedError("Document processing pipeline not yet implemented")


def main() -> None:
    """Main entry point for CLI."""
    args = parse_args()
    
    # Validate settings
    try:
        settings = get_settings()
    except Exception as e:
        print(f"Error loading configuration: {e}")
        print("Make sure you have a .env file with required settings.")
        sys.exit(1)
    
    # Validate paths
    input_path = validate_input(args.input)
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Run processing
    try:
        process_documents(input_path, output_path, args)
        print("Processing complete!")
    except NotImplementedError as e:
        print(f"Feature not implemented: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error during processing: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


# TODO: Add progress bar for batch processing
# TODO: Add parallel processing support
# TODO: Add resume capability for interrupted processing
# TODO: Add logging to file
