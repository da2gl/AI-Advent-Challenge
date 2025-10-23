#!/bin/bash

# Demo script for Code Analysis Pipeline
# Shows analysis of different code samples

echo "======================================================================"
echo "  CODE ANALYSIS PIPELINE DEMO"
echo "======================================================================"
echo ""
echo "This demo will analyze three different code samples:"
echo "  1. Good Python code (high quality)"
echo "  2. Bad Python code (needs improvement)"
echo "  3. JavaScript code"
echo ""
echo "Press Enter to start..."
read

echo ""
echo "======================================================================"
echo "SAMPLE 1: Well-written Python code"
echo "======================================================================"
echo ""
python3 analyze_code.py test_samples/sample1_good.py --no-ai --brief
echo ""
echo "Press Enter to continue..."
read

echo ""
echo "======================================================================"
echo "SAMPLE 2: Problematic Python code"
echo "======================================================================"
echo ""
python3 analyze_code.py test_samples/sample2_bad.py --no-ai --brief
echo ""
echo "Press Enter to continue..."
read

echo ""
echo "======================================================================"
echo "SAMPLE 3: JavaScript code"
echo "======================================================================"
echo ""
python3 analyze_code.py test_samples/sample3_javascript.js --no-ai --brief
echo ""
echo "======================================================================"
echo "Demo complete!"
echo ""
echo "To try interactive mode with AI:"
echo "  python3 chat.py"
echo "  > /analyze test_samples/sample1_good.py"
echo "  > Why is the quality score 99?"
echo "  > How can I improve this code?"
echo "======================================================================"
