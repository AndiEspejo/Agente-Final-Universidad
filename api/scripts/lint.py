#!/usr/bin/env python3
"""
Linting script for the Sales Inventory System.

This script runs all code quality tools:
- ruff (linting + import sorting)
- black (formatting)
- mypy (type checking)

Usage:
    python scripts/lint.py [--fix] [--check-only]
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str, capture_output: bool = False) -> bool:
    """Run a command and return True if successful."""
    print(f"\n🔧 {description}...")
    print(f"   Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        if result.returncode == 0:
            print(f"✅ {description} passed")
            if capture_output and result.stdout:
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} failed")
            if result.stdout:
                print(f"   stdout: {result.stdout}")
            if result.stderr:
                print(f"   stderr: {result.stderr}")
            return False

    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        return False


def main():
    """Main linting function."""
    parser = argparse.ArgumentParser(description="Run code quality tools")
    parser.add_argument(
        "--fix", action="store_true", help="Auto-fix issues where possible"
    )
    parser.add_argument(
        "--check-only", action="store_true", help="Only check, don't fix anything"
    )
    parser.add_argument("--fast", action="store_true", help="Skip slower checks (mypy)")

    args = parser.parse_args()

    print("🚀 Running code quality checks...")

    success = True

    # 1. Ruff linting and import sorting
    if args.fix and not args.check_only:
        success &= run_command(
            ["ruff", "check", ".", "--fix"], "Ruff linting (with fixes)"
        )
        success &= run_command(["ruff", "format", "."], "Ruff formatting")
    else:
        success &= run_command(["ruff", "check", "."], "Ruff linting (check only)")

    # 2. Black formatting
    if args.fix and not args.check_only:
        success &= run_command(["black", "."], "Black formatting")
    else:
        success &= run_command(["black", "--check", "."], "Black formatting check")

    # 3. MyPy type checking (optional for speed)
    if not args.fast:
        success &= run_command(
            ["mypy", ".", "--ignore-missing-imports"], "MyPy type checking"
        )
    else:
        print("\n⏩ Skipping MyPy (--fast mode)")

    # Summary
    print("\n" + "=" * 50)
    if success:
        print("🎉 All checks passed!")
        sys.exit(0)
    else:
        print("💥 Some checks failed!")
        if not args.fix:
            print("💡 Try running with --fix to auto-fix issues")
        sys.exit(1)


if __name__ == "__main__":
    main()
