#!/usr/bin/env python3
"""AWS CDK API MCP resource handlers."""

import logging
import os
from pathlib import Path
from typing import Optional


# Set up logging
logger = logging.getLogger(__name__)


# Define resource directories
DOCS_DIR = Path(__file__).parent.parent / "resources" / "aws-cdk" / "docs"
INTEG_TESTS_DIR = Path(__file__).parent.parent / "resources" / "aws-cdk" / "integ-tests"


async def get_cdk_api_docs(category: str, package_name: str, module_name: str, file_path: str) -> str:
    """Get AWS CDK API documentation from the resources directory.

    This resource handler serves documentation files from the resources/aws-cdk/docs directory.
    The files are organized by category, package and module.

    Example URIs:
    - cdk-api-docs://packages/@aws-cdk/aws-s3/README.md
    - cdk-api-docs://packages/aws-cdk-lib/aws-lambda/README.md
    - cdk-api-docs://root/DEPRECATED_APIs.md

    Args:
        category: The category (e.g., 'packages', 'root')
        package_name: The package name (e.g., '@aws-cdk', 'aws-cdk-lib')
        module_name: The module name (e.g., 'aws-s3', 'aws-lambda')
        file_path: The file path within the module (e.g., 'README.md')

    Returns:
        String containing the requested documentation
    """
    # Handle special case for root files like DEPRECATED_APIs.md
    if category == "root":
        file_path = os.path.join(DOCS_DIR, package_name)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return f"Error: File '{package_name}' not found"

    # For packages category, construct the file path
    if category == "packages":
        if file_path:
            file_path = os.path.join(DOCS_DIR, category, package_name, module_name, file_path)
        else:
            file_path = os.path.join(DOCS_DIR, category, package_name, module_name)
    else:
        # For other categories, construct the path accordingly
        if file_path:
            file_path = os.path.join(DOCS_DIR, category, package_name, module_name, file_path)
        else:
            file_path = os.path.join(DOCS_DIR, category, package_name, module_name)

    # Check if the file exists
    if os.path.exists(file_path):
        # If it's a directory, list the contents
        if os.path.isdir(file_path):
            files = os.listdir(file_path)
            result = f"# Contents of {package_name}/{module_name}\n\n"
            for f in sorted(files):
                if os.path.isdir(os.path.join(file_path, f)):
                    result += f"- [{f}/](cdk-api-docs://{category}/{package_name}/{module_name}/{f})\n"
                else:
                    result += f"- [{f}](cdk-api-docs://{category}/{package_name}/{module_name}/{f})\n"
            return result
        # If it's a file, return the contents
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    else:
        return f"Error: File '{file_path}' not found"


async def get_cdk_api_integ_tests(module_name: str, file_path: Optional[str] = None) -> str:
    """Get AWS CDK integration test examples from the resources directory.

    This resource handler serves integration test files from the resources/aws-cdk/integ-tests directory.
    The files are organized by module.

    Example URIs:
    - cdk-api-integ-tests://aws-s3/aws-s3.test1.md
    - cdk-api-integ-tests://aws-lambda/aws-lambda.handler.md

    Args:
        module_name: The module name (e.g., 'aws-s3', 'aws-lambda')
        file_path: The file path within the module (e.g., 'aws-s3.test1.md')

    Returns:
        String containing the requested integration test example
    """
    # Construct the file path
    if file_path:
        file_path = os.path.join(INTEG_TESTS_DIR, module_name, file_path)
    else:
        file_path = os.path.join(INTEG_TESTS_DIR, module_name)

    # Check if the file exists
    if os.path.exists(file_path):
        # If it's a directory, list the contents
        if os.path.isdir(file_path):
            files = os.listdir(file_path)
            result = f"# Integration Tests for {module_name}\n\n"
            for f in sorted(files):
                if os.path.isdir(os.path.join(file_path, f)):
                    result += f"- [{f}/](cdk-api-integ-tests://{module_name}/{f})\n"
                else:
                    result += f"- [{f}](cdk-api-integ-tests://{module_name}/{f})\n"
            return result
        # If it's a file, return the contents
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    else:
        return f"Error: File '{file_path}' not found"
