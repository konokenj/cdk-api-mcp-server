#!/usr/bin/env python3
"""
Main entry point for downloading repository data.
This script orchestrates the download process for multiple repositories.
"""

import argparse
import importlib
import sys
from pathlib import Path
from typing import List


def get_available_repos() -> List[str]:
    """
    Get a list of available repositories by scanning the same directory.

    Returns:
        List[str]: List of repository names
    """
    download_dir = Path(__file__).parent
    repos = []

    for item in download_dir.iterdir():
        if item.is_dir() and (item / "main.py").exists():
            repos.append(item.name)

    return repos


def download_repo(repo_name: str, force: bool = False) -> int:
    """
    Download data for a specific repository.

    Args:
        repo_name (str): Name of the repository
        force (bool): Force download even if the version is already processed

    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    try:
        # Import the repository's main module
        module_path = f"cdk_api_downloader.{repo_name}.main"
        module = importlib.import_module(module_path)

        # Call the download function with appropriate arguments
        if hasattr(module, "download"):
            # Check if the download function accepts a force parameter
            import inspect

            sig = inspect.signature(module.download)
            if "force" in sig.parameters:
                return module.download(force=force)
            else:
                return module.download()
        elif hasattr(module, "main"):
            # Try to call main with force parameter if it accepts it
            import inspect

            sig = inspect.signature(module.main)
            if "force" in sig.parameters:
                return module.main(force=force)
            else:
                return module.main()
        else:
            print(f"Error: No download or main function found in {module_path}")
            return 1
    except ImportError as e:
        print(f"Error importing module for repository '{repo_name}': {e}")
        return 1
    except Exception as e:
        print(f"Error downloading repository '{repo_name}': {e}")
        return 1


def main() -> int:
    """
    Main entry point for the download script.

    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(description="Download repository data")

    available_repos = get_available_repos()

    parser.add_argument(
        "--repos",
        nargs="+",
        choices=available_repos,
        default=available_repos,
        help="Repositories to download (default: all available repositories)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force download even if the version is already processed",
    )

    args = parser.parse_args()

    if not available_repos:
        print("No repositories found in directory")
        return 1

    exit_code = 0
    for repo in args.repos:
        print(f"Downloading {repo}...")
        # 強制フラグを渡す
        repo_exit_code = download_repo(repo, force=args.force)
        if repo_exit_code != 0:
            exit_code = repo_exit_code

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
