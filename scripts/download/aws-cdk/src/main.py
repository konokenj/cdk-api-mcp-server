import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlopen

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
OUT_DIR = "resources/aws-cdk"


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
        if work_path.exists():
            print(f"Cleaning existing directory: {WORK_DIR}")
            shutil.rmtree(WORK_DIR)
        
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


def process_repo_files():
    """
    Process the downloaded repository files.
    
    Returns:
        bool: True if processing was successful, False otherwise
    """
    try:
        print("Processing repository files...")
        
        # Create output directory if it doesn't exist
        os.makedirs(OUT_DIR, exist_ok=True)
        os.makedirs(f"{OUT_DIR}/docs", exist_ok=True)
        os.makedirs(f"{OUT_DIR}/integ-tests", exist_ok=True)
        
        # Process markdown files
        markdown_files = list(find_markdown_files(WORK_DIR))
        print(f"Found {len(markdown_files)} markdown files")
        for file in markdown_files:
            # remove prefix from source file path
            dist_path = file.replace(WORK_DIR + "/", "")
            # copy file to dist with same directory structure
            os.makedirs(os.path.dirname(f"{OUT_DIR}/docs/{dist_path}"), exist_ok=True)
            shutil.copy(file, f"{OUT_DIR}/docs/{dist_path}")
        
        # Process integration test files
        integ_test_files = list(find_integ_test_files(WORK_DIR))
        print(f"Found {len(integ_test_files)} integration test files")
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
        return True
    
    except Exception as e:
        print(f"Error processing repository files: {e}")
        return False


def download():
    """
    Download and process AWS CDK repository data.
    This function can be called from the main download script.
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    try:
        # Step 1: Download the repository
        if not download_github_repo():
            return 1
        
        # Step 2: Process the repository files
        if not process_repo_files():
            return 1
        
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
    return download()


if __name__ == "__main__":
    sys.exit(main())
