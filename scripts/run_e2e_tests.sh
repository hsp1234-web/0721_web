#!/bin/bash
#
# Phoenix Heart - Unified E2E Test Script
#
# This script is the single entry point for running all tests, including E2E tests.
#
# Flow:
# 1. Ensure our shell exits immediately on any error.
# 2. Find the project root directory.
# 3. Call the smart launcher `launch.py` in `--prepare-only` mode to
#    create the virtual environment and install all dependencies.
# 4. Start the services in the background.
# 5. Run the E2E test script.
# 6. Stop the services.
# 7. Run Pytest for unit/integration tests.
#

# Exit immediately on any error
set -e

# Get the script's directory and find the project root
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
PROJECT_ROOT="$SCRIPT_DIR/.."

echo "=== Phoenix Heart E2E Test Suite ==="

# Step 1: Prepare the test environment
echo
echo "--- Preparing environment (using launch.py --prepare-only) ---"
python3 "$PROJECT_ROOT/scripts/launch.py" --prepare-only

# Step 2: Start services in the background
echo
echo "--- Starting services in the background ---"
FINMIND_API_TOKEN="fake_token" python3 "$PROJECT_ROOT/scripts/launch.py" > server.log 2>&1 &
SERVER_PID=$!
sleep 5 # Give servers time to start

# Step 3: Run E2E tests
echo
echo "--- Running E2E tests ---"
python3 "$PROJECT_ROOT/e2e_test.py"

# Step 4: Stop services
echo
echo "--- Stopping services ---"
kill $SERVER_PID

# Step 5: Run Pytest
echo
echo "--- Running Pytest ---"
VENV_PYTHON="$PROJECT_ROOT/.venvs/base/bin/python"
"$VENV_PYTHON" -m pytest "$PROJECT_ROOT/src/"

echo
echo "✅ All tests completed successfully."
