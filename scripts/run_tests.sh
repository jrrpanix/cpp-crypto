#!/bin/bash
set -e

# Intelligently determine the test directory
# Check CI environment first, then local
if [ -d "/opt/cpp-crypto-deps/bin/tests" ]; then
  TEST_DIR="/opt/cpp-crypto-deps/bin/tests"
  echo "Using CI test directory: $TEST_DIR"
elif [ -d "/workspace/install/bin/tests" ]; then
  TEST_DIR="/workspace/install/bin/tests"
  echo "Using local test directory: $TEST_DIR"
elif [ -d "/workspace/apps/bin/tests" ]; then
  TEST_DIR="/workspace/apps/bin/tests"
  echo "Using legacy test directory: $TEST_DIR"
else
  echo "Test directory not found in any expected location:"
  echo "  - /opt/cpp-crypto-deps/bin/tests (CI)"
  echo "  - /workspace/install/bin/tests (local)"
  echo "  - /workspace/apps/bin/tests (legacy)"
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
