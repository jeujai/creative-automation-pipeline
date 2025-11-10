#!/bin/bash
# Validation script for Creative Automation Pipeline
# This script runs end-to-end validation tests

set -e

echo "=========================================="
echo "Creative Automation Pipeline Validation"
echo "=========================================="
echo ""

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  WARNING: OPENAI_API_KEY not set"
    echo "   Real API tests will be skipped"
    echo "   To run with real API: export OPENAI_API_KEY=your_key_here"
    echo ""
fi

# Run all integration tests
echo "Running integration tests..."
echo ""

python -m pytest tests/test_e2e_integration.py -v

echo ""
echo "=========================================="
echo "Validation Complete!"
echo "=========================================="
