import argparse
import os

import polars as pl


def view_parquet_columns(file_path: str):
    """
    Reads a Parquet file and prints its column names.
    """
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at '{file_path}'")
        return

    try:
        # Read just the schema without loading data to be faster
        schema = pl.read_parquet_schema(file_path)

        # Print the column names and their types
        print(f"📄 Schema for: {os.path.basename(file_path)}")
        print("-" * 40)
        for col_name, col_type in schema.items():
            print(f"  - {col_name}: {col_type}")
        print("-" * 40)

    except Exception as e:
        print(f"❌ An error occurred: {e}")


def main():
    """
    Main function to parse arguments and run the viewer.
    """
    parser = argparse.ArgumentParser(
        description="View the column names and types of a Parquet file."
    )
    parser.add_argument("parquet_file", type=str, help="Path to the Parquet file.")
    args = parser.parse_args()

    view_parquet_columns(args.parquet_file)


if __name__ == "__main__":
    main()
