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
    Get a list of available repositories by scanning the scripts/download directory.
    
    Returns:
        List[str]: List of repository names
    """
    download_dir = Path(__file__).parent
    repos = []
    
    for item in download_dir.iterdir():
        if item.is_dir() and (item / "src" / "main.py").exists():
            repos.append(item.name)
    
    return repos


def download_repo(repo_name: str) -> int:
    """
    Download data for a specific repository.
    
    Args:
        repo_name (str): Name of the repository
        
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    try:
        # Import the repository's main module
        module_path = f"scripts.download.{repo_name}.src.main"
        module = importlib.import_module(module_path)
        
        # Call the download function
        if hasattr(module, "download"):
            return module.download()
        elif hasattr(module, "main"):
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
        help="Repositories to download (default: all available repositories)"
    )
    
    args = parser.parse_args()
    
    if not available_repos:
        print("No repositories found in scripts/download directory")
        return 1
    
    exit_code = 0
    for repo in args.repos:
        print(f"Downloading {repo}...")
        repo_exit_code = download_repo(repo)
        if repo_exit_code != 0:
            exit_code = repo_exit_code
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
