import json
import os
import shutil
import sys
import tempfile
import zipfile
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.request import urlopen

import github
import semantic_version
from github import Github

from .aws_cdk import (
    find_integ_test_files,
    find_markdown_files,
    get_module_name,
    get_test_name,
    surround_with_codeblock,
)

# GitHub repository information
REPO_OWNER = "aws"
REPO_NAME = "aws-cdk"
REPO_BRANCH = "main"
GITHUB_DOWNLOAD_URL = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/archive/refs/heads/{REPO_BRANCH}.zip"

# Local directories
WORK_DIR = ".work/aws-cdk"
OUT_DIR = "cdk_api_mcp_server/resources/aws-cdk"
VERSION_DIR = "current-versions"
VERSION_FILE = f"{VERSION_DIR}/aws-cdk.txt"


def get_latest_release_version() -> Tuple[Optional[str], Optional[str]]:
    """
    Get the latest release version and timestamp from GitHub.
    
    Returns:
        Tuple[Optional[str], Optional[str]]: (Latest release version, UTC timestamp) or (None, None) if failed
    """
    try:
        print(f"Checking latest release version for {REPO_OWNER}/{REPO_NAME}...")
        g = Github()
        repo = g.get_repo(f"{REPO_OWNER}/{REPO_NAME}")
        latest_release = repo.get_latest_release()
        version = latest_release.tag_name
        # Convert published_at to UTC ISO format string
        timestamp = latest_release.published_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        print(f"Latest release version: {version} (published at: {timestamp})")
        return version, timestamp
    except Exception as e:
        print(f"Error getting latest release version: {e}")
        return None, None


def get_current_version_info() -> Dict:
    """
    Get the current processed version information from the version file.
    
    Returns:
        Dict: Current version information or empty dict if not found
    """
    try:
        if not os.path.exists(VERSION_FILE):
            print(f"Version file not found: {VERSION_FILE}")
            return {}
        
        with open(VERSION_FILE, "r") as f:
            version_data = json.load(f)
            version = version_data.get("version")
            timestamp = version_data.get("timestamp")
            markdown_files = version_data.get("markdown_files", 0)
            integ_test_files = version_data.get("integ_test_files", 0)
            
            print(f"Current processed version: {version} (processed at: {timestamp})")
            print(f"Previous file counts - Markdown: {markdown_files}, Integration tests: {integ_test_files}")
            
            return version_data
    except Exception as e:
        print(f"Error reading current version: {e}")
        return {}


def save_version_info(version: str, timestamp: str, markdown_files: int, integ_test_files: int) -> bool:
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
        current_timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        version_data = {
            "version": version,
            "timestamp": timestamp,
            "processed_at": current_timestamp,
            "markdown_files": markdown_files,
            "integ_test_files": integ_test_files
        }
        
        with open(VERSION_FILE, "w") as f:
            json.dump(version_data, f, indent=2)
        
        print(f"Version {version} saved to {VERSION_FILE}")
        return True
    except Exception as e:
        print(f"Error saving version: {e}")
        return False


def normalize_version(version_str: str) -> semantic_version.Version:
    """
    Normalize version string to semantic version.
    
    Args:
        version_str (str): Version string (e.g., 'v2.199.0')
        
    Returns:
        semantic_version.Version: Normalized semantic version
    """
    # Remove 'v' prefix if present
    if version_str.startswith('v'):
        version_str = version_str[1:]
    
    try:
        return semantic_version.Version(version_str)
    except ValueError:
        # If parsing fails, try to make it a valid semver
        parts = version_str.split('.')
        while len(parts) < 3:
            parts.append('0')
        
        # Take only the first three parts for semver
        version_str = '.'.join(parts[:3])
        return semantic_version.Version(version_str)


def is_update_needed() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Check if an update is needed by comparing versions using semantic versioning.
    
    Returns:
        Tuple[bool, Optional[str], Optional[str]]: (update_needed, latest_version, latest_timestamp)
    """
    latest_version_str, latest_timestamp = get_latest_release_version()
    current_info = get_current_version_info()
    
    if latest_version_str is None:
        print("Could not determine latest version, assuming update is needed")
        return True, None, None
    
    if not current_info:
        print("No current version found, update is needed")
        return True, latest_version_str, latest_timestamp
    
    current_version_str = current_info.get("version")
    current_timestamp = current_info.get("timestamp")
    
    if not current_version_str:
        print("Invalid current version information, update is needed")
        return True, latest_version_str, latest_timestamp
    
    # Compare using semantic versioning
    try:
        latest_version = normalize_version(latest_version_str)
        current_version = normalize_version(current_version_str)
        
        if latest_version > current_version:
            print(f"Version update needed: {current_version_str} -> {latest_version_str} (newer semantic version)")
            return True, latest_version_str, latest_timestamp
        
        # If versions are equal, compare timestamps
        if latest_version == current_version and current_timestamp and latest_timestamp:
            if latest_timestamp > current_timestamp:
                print(f"Version update needed: same version but newer release timestamp ({current_timestamp} -> {latest_timestamp})")
                return True, latest_version_str, latest_timestamp
    except Exception as e:
        print(f"Error comparing versions: {e}, falling back to string comparison")
        # Fall back to string comparison if semantic versioning fails
        if latest_version_str != current_version_str:
            print(f"Version update needed: {current_version_str} -> {latest_version_str} (string comparison)")
            return True, latest_version_str, latest_timestamp
    
    print(f"Already at latest version: {current_version_str}")
    return False, latest_version_str, latest_timestamp


def clean_output_directories():
    """
    Clean the output directories (resources/aws-cdk and .work/aws-cdk).
    
    Returns:
        bool: True if cleaning was successful, False otherwise
    """
    try:
        print("Cleaning output directories...")
        
        # Clean resources directory
        if os.path.exists(OUT_DIR):
            print(f"Removing existing directory: {OUT_DIR}")
            shutil.rmtree(OUT_DIR)
        
        # Clean work directory
        if os.path.exists(WORK_DIR):
            print(f"Removing existing directory: {WORK_DIR}")
            shutil.rmtree(WORK_DIR)
        
        # Create directories
        os.makedirs(OUT_DIR, exist_ok=True)
        os.makedirs(WORK_DIR, exist_ok=True)
        
        print("Output directories cleaned successfully")
        return True
    except Exception as e:
        print(f"Error cleaning output directories: {e}")
        return False


def download_github_repo():
    """
    Download the AWS CDK repository from GitHub.
    
    Returns:
        bool: True if download was successful, False otherwise
    """
    try:
        print(f"Downloading {REPO_OWNER}/{REPO_NAME} repository from GitHub...")
        
        # Create work directory if it doesn't exist
        work_path = Path(WORK_DIR)
        work_path.mkdir(parents=True, exist_ok=True)
        
        # Download the repository as a zip file
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_file:
            temp_path = temp_file.name
            
            print(f"Downloading from: {GITHUB_DOWNLOAD_URL}")
            with urlopen(GITHUB_DOWNLOAD_URL) as response:
                temp_file.write(response.read())
        
        try:
            # Extract the zip file
            print(f"Extracting repository to: {WORK_DIR}")
            with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                # The zip file contains a top-level directory with the repo name and branch
                # We need to extract the contents to our work directory
                for zip_info in zip_ref.infolist():
                    # Remove the top-level directory from the path
                    if "/" in zip_info.filename:
                        zip_info.filename = "/".join(zip_info.filename.split("/")[1:])
                        if zip_info.filename:  # Skip the empty path (top-level directory)
                            zip_ref.extract(zip_info, WORK_DIR)
            
            print(f"Repository successfully downloaded to: {WORK_DIR}")
            return True
        finally:
            # Clean up the temporary file
            os.unlink(temp_path)
    
    except Exception as e:
        print(f"Error downloading repository: {e}")
        return False


def process_repo_files() -> Tuple[bool, int, int]:
    """
    Process the downloaded repository files.
    
    Returns:
        Tuple[bool, int, int]: (success, markdown_files_count, integ_test_files_count)
    """
    try:
        print("Processing repository files...")
        
        # Create output directory if it doesn't exist
        os.makedirs(OUT_DIR, exist_ok=True)
        os.makedirs(f"{OUT_DIR}/docs", exist_ok=True)
        os.makedirs(f"{OUT_DIR}/integ-tests", exist_ok=True)
        
        # Process markdown files
        markdown_files = list(find_markdown_files(WORK_DIR))
        markdown_count = len(markdown_files)
        print(f"Found {markdown_count} markdown files")
        for file in markdown_files:
            # remove prefix from source file path
            dist_path = file.replace(WORK_DIR + "/", "")
            # copy file to dist with same directory structure
            os.makedirs(os.path.dirname(f"{OUT_DIR}/docs/{dist_path}"), exist_ok=True)
            shutil.copy(file, f"{OUT_DIR}/docs/{dist_path}")
        
        # Process integration test files
        integ_test_files = list(find_integ_test_files(WORK_DIR))
        integ_test_count = len(integ_test_files)
        print(f"Found {integ_test_count} integration test files")
        for file in integ_test_files:
            module_name = get_module_name(file)
            test_name = get_test_name(file)
            with open(file, "r") as f:
                content = f.read()
                os.makedirs(f"{OUT_DIR}/integ-tests/{module_name}", exist_ok=True)
                with open(
                    f"{OUT_DIR}/integ-tests/{module_name}/{module_name}.{test_name}.md", "w"
                ) as f:
                    f.write(surround_with_codeblock(module_name, test_name, content))
        
        print("Repository files processed successfully")
        return True, markdown_count, integ_test_count
    
    except Exception as e:
        print(f"Error processing repository files: {e}")
        return False, 0, 0


def check_file_count_decrease(current_info: Dict, markdown_count: int, integ_test_count: int) -> bool:
    """
    Check if the number of files has decreased compared to the previous run.
    
    Args:
        current_info (Dict): Current version information
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
        print(f"WARNING: Markdown files count decreased from {prev_markdown} to {markdown_count}")
    
    if integ_test_decreased:
        print(f"WARNING: Integration test files count decreased from {prev_integ_test} to {integ_test_count}")
    
    return markdown_decreased or integ_test_decreased


def download(force: bool = False):
    """
    Download and process AWS CDK repository data.
    This function can be called from the main download script.
    
    Args:
        force (bool): Force download even if the version is already processed
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    try:
        # Step 1: Get current version info
        current_info = get_current_version_info()
        
        # Step 2: Check if update is needed
        update_needed, latest_version, latest_timestamp = is_update_needed()
        
        if not update_needed and not force:
            print("Skipping download as no update is needed")
            return 0
        
        if force:
            print("Force flag is set, proceeding with download regardless of version")
            # 強制実行時は常に更新が必要と判断
            update_needed = True
        
        # Step 3: Clean output directories before proceeding
        if not clean_output_directories():
            return 1
        
        # Step 4: Download the repository
        if not download_github_repo():
            return 1
        
        # Step 5: Process the repository files
        success, markdown_count, integ_test_count = process_repo_files()
        if not success:
            return 1
        
        # Step 6: Check if file count has decreased
        if check_file_count_decrease(current_info, markdown_count, integ_test_count):
            print("WARNING: The number of processed files has decreased compared to the previous run.")
            print("This might indicate an issue with the repository or the download process.")
            print("Please check the repository and the download process.")
        
        # Step 7: Save the processed version
        if latest_version and latest_timestamp:
            if not save_version_info(latest_version, latest_timestamp, markdown_count, integ_test_count):
                print("Warning: Failed to save version information")
        
        print(f"AWS CDK repository data successfully downloaded and processed to: {OUT_DIR}")
        return 0
    
    except Exception as e:
        print(f"Error in download process: {e}")
        return 1


def main():
    """
    Main entry point when script is run directly.
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(description="Download AWS CDK repository data")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force download even if the version is already processed"
    )
    
    args = parser.parse_args()
    
    return download(force=args.force)


if __name__ == "__main__":
    import argparse
    sys.exit(main())
