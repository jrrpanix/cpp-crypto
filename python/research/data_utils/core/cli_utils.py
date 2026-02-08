"""
Common CLI argument parsers for data_utils scripts.
Reduces duplication across multiple command-line utilities.
"""

import argparse
from pathlib import Path


def add_io_args(parser: argparse.ArgumentParser, 
                input_default: str = None,
                output_default: str = None,
                input_help: str = "Input directory",
                output_help: str = "Output directory") -> None:
    """Add common input/output directory arguments."""
    if input_default:
        parser.add_argument(
            "--input-dir",
            type=str,
            default=input_default,
            help=f"{input_help} (default: {input_default})"
        )
    else:
        parser.add_argument(
            "--input-dir",
            type=str,
            required=True,
            help=input_help
        )
    
    if output_default:
        parser.add_argument(
            "--output-dir",
            type=str,
            default=output_default,
            help=f"{output_help} (default: {output_default})"
        )
    else:
        parser.add_argument(
            "--output-dir",
            type=str,
            required=True,
            help=output_help
        )


def add_dry_run_arg(parser: argparse.ArgumentParser) -> None:
    """Add --dry-run flag."""
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )


def add_symbol_filter_arg(parser: argparse.ArgumentParser, 
                          help_text: str = "Filter to specific symbol (e.g., BTCUSDT)") -> None:
    """Add --symbol filter argument."""
    parser.add_argument(
        "--symbol",
        type=str,
        help=help_text
    )


def add_date_range_args(parser: argparse.ArgumentParser,
                       start_required: bool = False,
                       end_required: bool = False) -> None:
    """Add --start-date and --end-date arguments."""
    parser.add_argument(
        "--start-date",
        type=str,
        required=start_required,
        help="Start date (YYYY-MM-DD format)"
    )
    parser.add_argument(
        "--end-date",
        type=str,
        required=end_required,
        help="End date (YYYY-MM-DD format)"
    )


def add_file_pattern_arg(parser: argparse.ArgumentParser,
                        default: str = "*.parquet") -> None:
    """Add --pattern argument for file matching."""
    parser.add_argument(
        "--pattern",
        type=str,
        default=default,
        help=f"File pattern to match (default: {default})"
    )


def add_verbosity_arg(parser: argparse.ArgumentParser) -> None:
    """Add --verbose flag."""
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output"
    )


def add_output_file_arg(parser: argparse.ArgumentParser,
                       default: str = None,
                       required: bool = False,
                       help_text: str = "Output file path") -> None:
    """Add --output-file argument."""
    if default:
        parser.add_argument(
            "--output-file",
            type=str,
            default=default,
            help=f"{help_text} (default: {default})"
        )
    else:
        parser.add_argument(
            "--output-file",
            type=str,
            required=required,
            help=help_text
        )


# Preset parser builders for common use cases

def create_transform_parser(description: str,
                           input_default: str = None,
                           output_default: str = None) -> argparse.ArgumentParser:
    """
    Create parser for data transformation scripts.
    Includes: input-dir, output-dir, dry-run, pattern, verbose
    """
    parser = argparse.ArgumentParser(description=description)
    add_io_args(parser, input_default, output_default)
    add_dry_run_arg(parser)
    add_file_pattern_arg(parser)
    add_verbosity_arg(parser)
    return parser


def create_analysis_parser(description: str,
                          input_default: str = None) -> argparse.ArgumentParser:
    """
    Create parser for analysis scripts.
    Includes: input-dir, symbol filter, date range, verbose
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--input-dir",
        type=str,
        default=input_default,
        help="Input directory" if not input_default else f"Input directory (default: {input_default})"
    )
    add_symbol_filter_arg(parser)
    add_date_range_args(parser)
    add_verbosity_arg(parser)
    return parser


def add_dir_arg(
    parser: argparse.ArgumentParser,
    name: str,
    default: str = None,
    required: bool = False,
    help_text: str = None
) -> None:
    """
    Add a directory argument with consistent naming patterns.
    
    Args:
        parser: ArgumentParser to add argument to
        name: Directory argument name (e.g., 'kline-dir', 'download-dir')
        default: Default directory path (optional)
        required: Whether the argument is required
        help_text: Custom help text (optional)
        
    Example:
        add_dir_arg(parser, "kline-dir", required=True, help_text="Directory containing kline files")
        add_dir_arg(parser, "aggregate-dir", default="/workspace/data/klines_aggregate")
    """
    arg_name = f"--{name}"
    if help_text is None:
        help_text = f"Directory path for {name.replace('-', ' ')}"
    if default:
        help_text += f" (default: {default})"
    
    parser.add_argument(
        arg_name,
        type=str,
        default=default,
        required=required,
        help=help_text
    )


__all__ = [
    "add_io_args",
    "add_dry_run_arg",
    "add_symbol_filter_arg",
    "add_date_range_args",
    "add_file_pattern_arg",
    "add_verbosity_arg",
    "add_output_file_arg",
    "add_dir_arg",
    "create_transform_parser",
    "create_analysis_parser",
]
