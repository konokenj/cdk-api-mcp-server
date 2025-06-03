from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any
from urllib.request import urlopen

import semantic_version  # type: ignore
from github import Github

from cdk_api_downloader.aws_cdk.aws_cdk import (
    find_integ_test_files,
    find_markdown_files,
    normalize_output_path,
)

# ロガーの設定
logger = logging.getLogger(__name__)

# GitHub repository information
REPO_OWNER = "aws"
REPO_NAME = "aws-cdk"
REPO_BRANCH = "main"
GITHUB_DOWNLOAD_URL = (
    f"https://github.com/{REPO_OWNER}/{REPO_NAME}/archive/refs/heads/{REPO_BRANCH}.zip"
)

# Local directories
WORK_DIR = ".work/aws-cdk"
OUT_DIR = "cdk_api_mcp_server/resources/aws-cdk"
VERSION_DIR = "current-versions"
VERSION_FILE = f"{VERSION_DIR}/aws-cdk.txt"

# 定数
MIN_VERSION_PARTS = 3  # セマンティックバージョンの最小パーツ数


def get_latest_release_version() -> tuple[str | None, str | None]:
    """
    Get the latest release version and timestamp from GitHub.

    Returns:
        tuple[str | None, str | None]: (Latest release version, UTC timestamp) or (None, None) if failed
    """
    try:
        g = Github()
        repo = g.get_repo(f"{REPO_OWNER}/{REPO_NAME}")
        latest_release = repo.get_latest_release()
        version = latest_release.tag_name
        # Convert published_at to UTC ISO format string
        timestamp = latest_release.published_at.strftime("%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, AttributeError, ConnectionError):
        logger.exception("Failed to get latest release")
        return None, None

    return version, timestamp


def get_current_version_info() -> dict[str, Any]:
    """
    Get the current processed version information from the version file.

    Returns:
        dict[str, Any]: Current version information or empty dict if not found
    """
    try:
        if not os.path.exists(VERSION_FILE):
            return {}

        with open(VERSION_FILE) as f:
            version_data = json.load(f)
            version_data.get("version")
            version_data.get("timestamp")
            version_data.get("markdown_files", 0)
            version_data.get("integ_test_files", 0)

            return version_data
    except (OSError, json.JSONDecodeError):
        logger.exception("Failed to read version file")
        return {}


def save_version_info(
    version: str, timestamp: str, markdown_files: int, integ_test_files: int
) -> bool:
    """
    Save the processed version information to the version file.

    Args:
        version (str): Version to save
        timestamp (str): UTC timestamp of the release
        markdown_files (int): Number of markdown files processed
        integ_test_files (int): Number of integration test files processed

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        os.makedirs(VERSION_DIR, exist_ok=True)

        # Current UTC timestamp
        current_timestamp = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        version_data = {
            "version": version,
            "timestamp": timestamp,
            "processed_at": current_timestamp,
            "markdown_files": markdown_files,
            "integ_test_files": integ_test_files,
        }
    except OSError:
        logger.exception("Failed to prepare version info")
        return False

    try:
        with open(VERSION_FILE, "w") as f:
            json.dump(version_data, f, indent=2)
    except OSError:
        logger.exception("Failed to save version info")
        return False

    return True


def normalize_version(version_str: str) -> semantic_version.Version:
    """
    Normalize version string to semantic version.

    Args:
        version_str (str): Version string (e.g., 'v2.199.0')

    Returns:
        semantic_version.Version: Normalized semantic version
    """
    # Remove 'v' prefix if present
    if version_str.startswith("v"):
        version_str = version_str[1:]

    try:
        return semantic_version.Version(version_str)
    except ValueError:
        # If parsing fails, try to make it a valid semver
        parts = version_str.split(".")
        while len(parts) < MIN_VERSION_PARTS:
            parts.append("0")

        # Take only the first three parts for semver
        version_str = ".".join(parts[:3])
        return semantic_version.Version(version_str)


def is_update_needed() -> tuple[bool, str | None, str | None]:
    """
    Check if an update is needed by comparing versions using semantic versioning.

    Returns:
        Tuple[bool, Optional[str], Optional[str]]: (update_needed, latest_version, latest_timestamp)
    """
    latest_version_str, latest_timestamp = get_latest_release_version()
    current_info = get_current_version_info()

    if latest_version_str is None:
        return True, None, None

    if not current_info:
        return True, latest_version_str, latest_timestamp

    current_version_str = current_info.get("version")
    current_timestamp = current_info.get("timestamp")

    if not current_version_str:
        return True, latest_version_str, latest_timestamp

    try:
        # Compare using semantic versioning
        latest_version = normalize_version(latest_version_str)
        current_version = normalize_version(current_version_str)

        if latest_version > current_version:
            return True, latest_version_str, latest_timestamp

        # If versions are equal, compare timestamps
        if (
            latest_version == current_version
            and current_timestamp
            and latest_timestamp
            and latest_timestamp > current_timestamp
        ):
            return True, latest_version_str, latest_timestamp
    except (ValueError, TypeError):
        # Fall back to string comparison if semantic versioning fails
        logger.warning(
            "Failed to compare versions semantically, falling back to string comparison"
        )
        if latest_version_str != current_version_str:
            return True, latest_version_str, latest_timestamp

    return False, latest_version_str, latest_timestamp


def clean_output_directories():
    """
    Clean the output directories (resources/aws-cdk and .work/aws-cdk).

    Returns:
        bool: True if cleaning was successful, False otherwise
    """
    try:
        # Clean resources directory
        if os.path.exists(OUT_DIR):
            shutil.rmtree(OUT_DIR)

        # Clean work directory
        if os.path.exists(WORK_DIR):
            shutil.rmtree(WORK_DIR)
    except (OSError, PermissionError):
        logger.exception("Failed to clean directories")
        return False

    try:
        # Create directories
        os.makedirs(OUT_DIR, exist_ok=True)
        os.makedirs(WORK_DIR, exist_ok=True)
    except OSError:
        logger.exception("Failed to create directories")
        return False

    return True


def _raise_url_error(invalid_url: str, error_type: str = "insecure") -> None:
    """
    共通のURL関連エラーを発生させる関数

    Args:
        invalid_url (str): 無効なURL
        error_type (str): エラータイプ ("insecure" または "https_required")

    Raises:
        ValueError: URLが無効な場合
    """
    if error_type == "insecure":
        error_msg = f"Insecure URL scheme: {invalid_url}"
    else:
        error_msg = f"Only HTTPS URLs are allowed: {invalid_url}"

    logger.error(error_msg)
    raise ValueError(error_msg)


def validate_url(url: str) -> None:
    """
    Validate that the URL uses a secure scheme.

    Args:
        url (str): URL to validate

    Raises:
        ValueError: If the URL does not use https scheme
    """
    if not url.startswith("https://"):
        _raise_url_error(url, "insecure")


def download_github_repo():
    """
    Download the AWS CDK repository from GitHub.

    Returns:
        bool: True if download was successful, False otherwise
    """
    temp_path = None
    try:
        # Create work directory if it doesn't exist
        work_path = Path(WORK_DIR)
        work_path.mkdir(parents=True, exist_ok=True)

        # Download the repository as a zip file
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_file:
            temp_path = temp_file.name

            # Use https scheme only for security
            validate_url(GITHUB_DOWNLOAD_URL)

            # S310: Use explicit scheme validation for urlopen
            if not GITHUB_DOWNLOAD_URL.startswith("https://"):
                _raise_url_error(GITHUB_DOWNLOAD_URL, "https_required")

            with urlopen(GITHUB_DOWNLOAD_URL) as response:  # noqa: S310
                temp_file.write(response.read())

        try:
            # Extract the zip file
            with zipfile.ZipFile(temp_path, "r") as zip_ref:
                # The zip file contains a top-level directory with the repo name and branch
                # We need to extract the contents to our work directory
                for zip_info in zip_ref.infolist():
                    # Remove the top-level directory from the path
                    if "/" in zip_info.filename:
                        zip_info.filename = "/".join(zip_info.filename.split("/")[1:])
                        if (
                            zip_info.filename
                        ):  # Skip the empty path (top-level directory)
                            zip_ref.extract(zip_info, WORK_DIR)
        finally:
            # Clean up the temporary file
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

    except (OSError, zipfile.BadZipFile, ValueError):
        logger.exception("Failed to download repository")
        return False
    else:
        return True


def process_repo_files() -> tuple[bool, int, int]:
    """
    Process the downloaded repository files.

    Returns:
        tuple[bool, int, int]: (success, markdown_files_count, integ_test_files_count)
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(OUT_DIR, exist_ok=True)

        # Process markdown files
        markdown_files = list(find_markdown_files(WORK_DIR))
        markdown_count = len(markdown_files)
    except OSError:
        logger.exception("Failed to prepare directories")
        return False, 0, 0

    try:
        for file in markdown_files:
            # 標準化されたパスを取得
            normalized_path = normalize_output_path(file)
            output_file = f"{OUT_DIR}/{normalized_path}"

            # 出力先ディレクトリを作成
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            # ファイルをコピー
            shutil.copy(file, output_file)
    except OSError:
        logger.exception("Failed to process markdown files")
        return False, 0, 0

    try:
        # Process integration test files
        integ_test_files = list(find_integ_test_files(WORK_DIR))
        integ_test_count = len(integ_test_files)
    except OSError:
        logger.exception("Failed to find integration test files")
        return False, markdown_count, 0

    try:
        for file in integ_test_files:
            # 標準化されたパスを取得
            normalized_path = normalize_output_path(file)
            output_file = f"{OUT_DIR}/{normalized_path}"

            # 出力先ディレクトリを作成
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            # ファイル内容を読み込み、そのままコピー（マークダウン修飾なし）
            with open(file, encoding="utf-8") as f:
                content = f.read()
                with open(output_file, "w", encoding="utf-8") as out_f:
                    out_f.write(content)
    except OSError:
        logger.exception("Failed to process integration test files")
        return False, markdown_count, 0

    return True, markdown_count, integ_test_count


def check_file_count_decrease(
    current_info: dict[str, Any], markdown_count: int, integ_test_count: int
) -> bool:
    """
    Check if the number of files has decreased compared to the previous run.

    Args:
        current_info (dict[str, Any]): Current version information
        markdown_count (int): Current markdown files count
        integ_test_count (int): Current integration test files count

    Returns:
        bool: True if file count has decreased, False otherwise
    """
    if not current_info:
        return False

    prev_markdown = current_info.get("markdown_files", 0)
    prev_integ_test = current_info.get("integ_test_files", 0)

    markdown_decreased = markdown_count < prev_markdown
    integ_test_decreased = integ_test_count < prev_integ_test

    if markdown_decreased:
        logger.warning(
            "Markdown file count decreased from %d to %d", prev_markdown, markdown_count
        )

    if integ_test_decreased:
        logger.warning(
            "Integration test file count decreased from %d to %d",
            prev_integ_test,
            integ_test_count,
        )

    return markdown_decreased or integ_test_decreased


def download():
    """
    Download and process AWS CDK repository data.
    This function can be called from the main download script.
    Always downloads regardless of whether updates are available.

    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    try:
        # Step 1: Get current version info
        current_info = get_current_version_info()

        # Step 2: 常に更新を実行
        logger.info("Performing download without version check")
        latest_version, latest_timestamp = get_latest_release_version()

        # Step 3: Clean output directories before proceeding
        if not clean_output_directories():
            logger.error("Failed to clean output directories")
            return 1

        # Step 4: Download the repository
        if not download_github_repo():
            logger.error("Failed to download repository")
            return 1

        # Step 5: Process the repository files
        success, markdown_count, integ_test_count = process_repo_files()
        if not success:
            logger.error("Failed to process repository files")
            return 1

        # Step 6: Check if file count has decreased
        if check_file_count_decrease(current_info, markdown_count, integ_test_count):
            logger.warning("File count has decreased, but continuing with update")

        # Step 7: Save the processed version
        if latest_version and latest_timestamp:
            if not save_version_info(
                latest_version, latest_timestamp, markdown_count, integ_test_count
            ):
                logger.error("Failed to save version information")
                return 1
            logger.info(
                "Successfully updated to version %s with %d markdown files and %d integration test files",
                latest_version,
                markdown_count,
                integ_test_count,
            )

    except (OSError, ValueError, ConnectionError):
        logger.exception("An unexpected error occurred")
        return 1
    else:
        return 0


def check_for_updates():
    """
    Check if updates are available without downloading.

    Returns:
        int: Exit code (0 if updates are available, 1 if no updates are available or error occurred)
    """
    try:
        update_needed, latest_version, _ = is_update_needed()
        if update_needed:
            logger.info("Updates are available: %s", latest_version)
            return 0  # 更新があれば成功として終了
        else:
            logger.info("No updates available")
            return 1  # 更新がなければ終了コード1で終了
    except Exception:
        logger.exception("Error checking for updates")
        return 1  # エラーの場合も終了コード1


def main():
    """
    Main entry point when script is run directly.

    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(description="Download AWS CDK repository data")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only check if updates are available without downloading",
    )

    args = parser.parse_args()

    if args.check:
        return check_for_updates()
    else:
        return download()


if __name__ == "__main__":
    import argparse

    sys.exit(main())
