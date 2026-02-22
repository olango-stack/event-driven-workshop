#!/bin/bash
# MIT No Attribution - Copyright 2025 Amazon Web Services, Inc.
# Script to run pylint on all Python files in the project
# This script uses the .pylintrc configuration file which disables line-too-long warnings

set -e

echo "🔍 Running pylint on all Python files..."
echo "📋 Using configuration from .pylintrc (line-too-long disabled)"
echo "=================================================="

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "🐍 Activating virtual environment..."
    source .venv/bin/activate
fi

# Check if pylint is installed
if ! command -v pylint &> /dev/null; then
    echo "❌ pylint not found. Installing..."
    pip install pylint==3.3.7
fi

# Find all Python files and run pylint
echo "🔍 Scanning for Python files..."
python_files=$(find . -name "*.py" -not -path "./.venv/*" -not -path "./cdk.out/*" -not -path "./__pycache__/*")

if [ -z "$python_files" ]; then
    echo "❌ No Python files found"
    exit 1
fi

echo "📁 Found Python files:"
echo "$python_files"
echo "=================================================="

# Run pylint on each file
exit_code=0
for file in $python_files; do
    echo "🔍 Checking: $file"
    if ! pylint "$file" --reports=no; then
        exit_code=1
    fi
    echo "------------------------------------------------"
done

if [ $exit_code -eq 0 ]; then
    echo "✅ All files passed pylint checks!"
else
    echo "❌ Some files have pylint issues (but line-too-long is disabled as configured)"
fi

exit $exit_code
