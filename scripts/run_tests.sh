#!/bin/bash
set -e

TEST_DIR="/workspace/apps/bin/tests"

if [ ! -d "$TEST_DIR" ]; then
  echo "Test directory not found: $TEST_DIR"
  echo "Please ensure you have run 'make build-code' first."
  exit 1
fi

# Find and run all test executables
for test_exe in $(find "$TEST_DIR" -type f -executable); do
  echo "=================================================="
  echo "Running test: $(basename "$test_exe")"
  echo "=================================================="
  "$test_exe"
  echo ""
done

echo "✅ All tests passed successfully."
