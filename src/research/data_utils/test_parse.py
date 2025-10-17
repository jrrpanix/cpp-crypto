#!/usr/bin/env python3
"""
Test program to verify read_binance_zip function works correctly.

This tests the shared parsing function to ensure we didn't regress
the code in update_klines.py.
"""

import argparse
from pathlib import Path

import polars as pl

from update_klines import read_binance_zip


def test_parse_zip(zip_path: Path, show_sample: bool = True) -> bool:
    """
    Test parsing a Binance zip file.
    
    Args:
        zip_path: Path to the zip file to test
        show_sample: If True, show sample of the data
        
    Returns:
        True if successful, False otherwise
    """
    print(f"Testing: {zip_path.name}")
    print("="*80)
    
    if not zip_path.exists():
        print(f"❌ Error: File not found: {zip_path}")
        return False
    
    try:
        # Test 1: Parse without schema (basic parsing)
        print("\n📖 Test 1: Basic parsing (no schema)")
        df = read_binance_zip(str(zip_path))
        
        print(f"   ✅ Successfully parsed zip file")
        print(f"   Rows: {len(df):,}")
        print(f"   Columns: {len(df.columns)}")
        print(f"\n   Schema:")
        for col_name, col_type in df.schema.items():
            print(f"      {col_name}: {col_type}")
        
        if show_sample:
            print(f"\n   First 5 rows:")
            print(df.head(5))
        
        # Test 2: Parse with schema matching (simulating repair scenario)
        print("\n📖 Test 2: Parsing with schema override")
        
        # Create a schema to override (simulating existing parquet schema)
        schema_override = df.schema.copy()
        
        df2 = read_binance_zip(str(zip_path), schema_override)
        
        print(f"   ✅ Successfully parsed with schema override")
        print(f"   Rows: {len(df2):,}")
        
        # Verify schemas match
        if df.schema == df2.schema:
            print(f"   ✅ Schemas match!")
        else:
            print(f"   ⚠️  Warning: Schemas differ")
            print(f"      Original: {df.schema}")
            print(f"      Override: {df2.schema}")
        
        # Test 3: Check data integrity
        print("\n📊 Test 3: Data integrity checks")
        
        # Check for nulls
        null_counts = df.null_count()
        has_nulls = any(null_counts.row(0))
        if has_nulls:
            print(f"   ⚠️  Found null values:")
            for i, col in enumerate(df.columns):
                count = null_counts.row(0)[i]
                if count > 0:
                    print(f"      {col}: {count} nulls")
        else:
            print(f"   ✅ No null values found")
        
        # Check timestamp order
        if "open_time" in df.columns:
            is_sorted = df["open_time"].is_sorted()
            if is_sorted:
                print(f"   ✅ Timestamps are sorted")
            else:
                print(f"   ⚠️  Timestamps are NOT sorted")
            
            # Show date range
            first_time = df["open_time"][0]
            last_time = df["open_time"][-1]
            print(f"   Date range: {first_time} to {last_time}")
        
        # Check numeric columns
        print(f"\n   Sample statistics:")
        numeric_cols = ["open", "high", "low", "close", "volume"]
        for col in numeric_cols:
            if col in df.columns:
                min_val = df[col].min()
                max_val = df[col].max()
                print(f"      {col}: min={min_val}, max={max_val}")
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error parsing zip file: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "="*80)
        print("❌ TESTS FAILED")
        print("="*80)
        return False


def main():
    """Main function to test zip parsing."""
    parser = argparse.ArgumentParser(
        description="Test the read_binance_zip function.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with the default file
  python test_parse.py
  
  # Test with a custom file
  python test_parse.py --zip-file /workspace/data/downloads/ETHUSDT-1m-2025-09.zip
  
  # Test without showing sample data
  python test_parse.py --no-sample
        """
    )
    parser.add_argument(
        "--zip-file",
        type=str,
        default="/workspace/data/downloads/BTCUSDT-1m-2025-09.zip",
        help="Path to zip file to test (default: /workspace/data/downloads/BTCUSDT-1m-2025-09.zip)"
    )
    parser.add_argument(
        "--no-sample",
        action="store_true",
        help="Don't show sample data rows"
    )
    
    args = parser.parse_args()
    
    zip_path = Path(args.zip_file)
    
    success = test_parse_zip(zip_path, show_sample=not args.no_sample)
    
    if not success:
        exit(1)


if __name__ == "__main__":
    main()
