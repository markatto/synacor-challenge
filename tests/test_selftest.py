#!/usr/bin/env python3
"""Test that the selftest completes successfully with the expected flag."""

import subprocess
import sys
from pathlib import Path

def test_selftest_completion():
    """Test that the selftest runs and produces the zwrItUhCFSTC flag."""
    # Run the interpreter with empty input to trigger selftest
    result = subprocess.run(
        [sys.executable, 'interpreter.py'],
        input='',
        text=True,
        capture_output=True,
        cwd=Path(__file__).parent.parent
    )

    # Check that it completed successfully
    assert result.returncode == 0, f"Selftest failed with return code {result.returncode}"

    # Check that the completion message appears
    assert "self-test complete, all tests pass" in result.stdout, "Selftest completion message not found"

    # Check that the expected flag appears
    assert "zwrItUhCFSTC" in result.stdout, "Expected selftest flag 'zwrItUhCFSTC' not found"

    print("✓ Selftest completed successfully with flag: zwrItUhCFSTC")

if __name__ == "__main__":
    test_selftest_completion()