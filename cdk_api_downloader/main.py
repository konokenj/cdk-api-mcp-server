"""
Main entry point for downloading repository data.
This script orchestrates the download process for multiple repositories.
"""

from __future__ import annotations

import argparse
import importlib
import json
import logging
import sys
from pathlib import Path
from typing import List

# ロガーの設定
logger = logging.getLogger(__name__)


def get_available_repos() -> List[str]:
    """
    Get a list of available repositories by scanning the same directory.

    Returns:
        list[str]: List of repository names
    """
    download_dir = Path(__file__).parent

    return [
        item.name
        for item in download_dir.iterdir()
        if item.is_dir() and (item / "main.py").exists()
    ]


def download_repo(repo_name: str, *, force: bool = False) -> int:
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
            return module.download()

        # Try to call main with force parameter if it accepts it
        import inspect

        sig = inspect.signature(module.main)
        if "force" in sig.parameters:
            return module.main(force=force)
        return module.main()
    except ImportError:
        logger.exception("Error importing module %s", module_path)
        return 1
    except (AttributeError, TypeError, ValueError):
        logger.exception("Error calling download function for %s", repo_name)
        return 1


def main() -> int:
    """
    Main entry point for the download script.

    Returns:
        int: Always returns 0 (success)
        JSONを標準出力に返します: {"update-required": true|false, "updated-libraries": ["aws-cdk", ...]}
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
        "--check",
        action="store_true",
        help="Only check if updates are available without downloading",
    )

    args = parser.parse_args()

    if not available_repos:
        return 1  # 利用可能なリポジトリがない場合のみエラー

    # 更新確認のみのモード
    if args.check:
        updates_required = False
        updated_libraries = []

        for repo in args.repos:
            try:
                # Import the repository's main module
                module_path = f"cdk_api_downloader.{repo}.main"
                module = importlib.import_module(module_path)

                # Call is_update_needed if available
                if hasattr(module, "is_update_needed"):
                    update_needed, _, _ = module.is_update_needed()
                    if update_needed:
                        logger.info("Updates are available for %s", repo)
                        updates_required = True
                        updated_libraries.append(repo)
                    else:
                        logger.info("No updates available for %s", repo)
            except Exception:
                logger.exception("Error checking updates for %s", repo)

        # JSON形式で結果を出力
        result = {
            "update-required": updates_required,
            "updated-libraries": updated_libraries,
        }
        print(json.dumps(result))

        # アップデートの有無に関わらず常に成功を返す
        return 0

    # 通常のダウンロードモード（常に更新を確認せず実行）
    exit_code = 0
    for repo in args.repos:
        # 常に強制実行
        repo_exit_code = download_repo(repo, force=True)
        if repo_exit_code != 0:
            exit_code = repo_exit_code

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
