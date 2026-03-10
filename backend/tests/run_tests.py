#!/usr/bin/env python3
"""
Test runner script
"""
import sys
import pytest

if __name__ == "__main__":
    # Run tests with coverage
    args = [
        "tests/",
        "-v",
        "--cov=src",
        "--cov-report=html",
        "--cov-report=term",
        "--cov-fail-under=80"
    ]
    
    exit_code = pytest.main(args)
    sys.exit(exit_code)