#!/usr/bin/env python3
"""AWS CDK API MCP server implementation."""

import logging
import os
import json
from pathlib import Path
from cdk_api_mcp_server.core import resources
from fastmcp import FastMCP
from fastmcp.resources import TextResource, DirectoryResource


# Set up logging
logger = logging.getLogger(__name__)


# Define resource directories
DOCS_DIR = Path(__file__).parent.parent / "resources" / "aws-cdk" / "docs"
INTEG_TESTS_DIR = Path(__file__).parent.parent / "resources" / "aws-cdk" / "integ-tests"


# Create MCP server
mcp = FastMCP(
    'AWS CDK API MCP Server',
    dependencies=[],
)


# Register resource templates for hierarchical navigation
@mcp.resource('cdk-api-docs://')
async def list_root_categories():
    """List all available categories in the CDK API documentation."""
    if not DOCS_DIR.exists():
        return {"error": "Documentation directory not found"}
    
    categories = []
    # Add root category
    categories.append({
        "name": "root",
        "uri": "cdk-api-docs://root/",
        "description": "Root level documentation files",
        "is_directory": True
    })
    
    # Add packages category if it exists
    packages_dir = DOCS_DIR / "packages"
    if packages_dir.exists() and packages_dir.is_dir():
        categories.append({
            "name": "packages",
            "uri": "cdk-api-docs://packages/",
            "description": "AWS CDK packages documentation",
            "is_directory": True
        })
    
    return json.dumps({"categories": categories})


@mcp.resource('cdk-api-docs://root/')
def list_root_files():
    """List all files in the root directory of the CDK API documentation."""
    if not DOCS_DIR.exists():
        return {"error": "Documentation directory not found"}
    
    files = []
    for item in DOCS_DIR.iterdir():
        if item.is_file():
            files.append({
                "name": item.name,
                "uri": f"cdk-api-docs://root/{item.name}",
                "is_directory": False
            })
        elif item.is_dir() and item.name != "packages":  # Skip packages dir as it's handled separately
            files.append({
                "name": item.name,
                "uri": f"cdk-api-docs://root/{item.name}/",
                "is_directory": True
            })
    
    return json.dumps({"files": files})


@mcp.resource('cdk-api-docs://root/{file_name}')
def get_root_file(file_name: str):
    """Get a file from the root directory of the CDK API documentation."""
    file_path = DOCS_DIR / file_name
    
    if not file_path.exists() or not file_path.is_file():
        return f"Error: File '{file_name}' not found"
    
    # Read the file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create and return a TextResource
    return TextResource(
        uri=f"cdk-api-docs://root/{file_name}",
        name=file_name,
        text=content,
        description=f"Root documentation file: {file_name}",
        mime_type="text/markdown" if file_name.endswith(".md") else "text/plain"
    )


@mcp.resource('cdk-api-docs://packages/')
def list_packages():
    """List all packages in the CDK API documentation."""
    packages_dir = DOCS_DIR / "packages"
    
    if not packages_dir.exists() or not packages_dir.is_dir():
        return {"error": "Packages directory not found"}
    
    packages = []
    for item in packages_dir.iterdir():
        if item.is_dir():
            packages.append({
                "name": item.name,
                "uri": f"cdk-api-docs://packages/{item.name}/",
                "is_directory": True
            })
    
    return json.dumps({"packages": packages})


@mcp.resource('cdk-api-docs://packages/{package_name}/')
def list_package_modules(package_name: str):
    """List all modules in a specific package."""
    package_dir = DOCS_DIR / "packages" / package_name
    
    if not package_dir.exists() or not package_dir.is_dir():
        return {"error": f"Package '{package_name}' not found"}
    
    modules = []
    for item in package_dir.iterdir():
        if item.is_dir():
            modules.append({
                "name": item.name,
                "uri": f"cdk-api-docs://packages/{package_name}/{item.name}/",
                "is_directory": True
            })
        elif item.is_file():
            modules.append({
                "name": item.name,
                "uri": f"cdk-api-docs://packages/{package_name}/{item.name}",
                "is_directory": False
            })
    
    return json.dumps({"modules": modules})


@mcp.resource('cdk-api-docs://packages/{package_name}/{module_name}/')
def list_module_files(package_name: str, module_name: str):
    """List all files in a specific module."""
    module_dir = DOCS_DIR / "packages" / package_name / module_name
    
    if not module_dir.exists() or not module_dir.is_dir():
        return {"error": f"Module '{module_name}' not found in package '{package_name}'"}
    
    # ここでのみDirectoryResourceを使用
    return DirectoryResource(
        uri=f"cdk-api-docs://packages/{package_name}/{module_name}/",
        name=f"Files in {package_name}/{module_name}",
        path=module_dir,
        description=f"List of files in the {package_name}/{module_name} module",
        recursive=False
    )


@mcp.resource('cdk-api-docs://packages/{package_name}/{module_name}/{file_path}')
def get_module_file(package_name: str, module_name: str, file_path: str):
    """Get a specific file from a module."""
    file_full_path = DOCS_DIR / "packages" / package_name / module_name / file_path
    
    if not file_full_path.exists() or not file_full_path.is_file():
        return f"Error: File '{file_path}' not found in {package_name}/{module_name}"
    
    # Read the file content
    with open(file_full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create and return a TextResource
    return TextResource(
        uri=f"cdk-api-docs://packages/{package_name}/{module_name}/{file_path}",
        name=file_path,
        text=content,
        description=f"Documentation file: {file_path} in {package_name}/{module_name}",
        mime_type="text/markdown" if file_path.endswith(".md") else "text/plain"
    )


# Register integration tests resources
@mcp.resource('cdk-api-integ-tests://')
def list_integ_test_modules():
    """List all modules with integration tests."""
    if not INTEG_TESTS_DIR.exists():
        return {"error": "Integration tests directory not found"}
    
    modules = []
    for item in INTEG_TESTS_DIR.iterdir():
        if item.is_dir():
            modules.append({
                "name": item.name,
                "uri": f"cdk-api-integ-tests://{item.name}/",
                "is_directory": True
            })
    
    return json.dumps({"modules": modules})


@mcp.resource('cdk-api-integ-tests://{module_name}/')
def list_module_tests(module_name: str):
    """List all integration tests for a specific module."""
    module_dir = INTEG_TESTS_DIR / module_name
    
    if not module_dir.exists() or not module_dir.is_dir():
        return {"error": f"Module '{module_name}' not found in integration tests"}
    
    # ここでのみDirectoryResourceを使用
    return DirectoryResource(
        uri=f"cdk-api-integ-tests://{module_name}/",
        name=f"Integration tests for {module_name}",
        path=module_dir,
        description=f"List of integration tests for the {module_name} module",
        recursive=False
    )


@mcp.resource('cdk-api-integ-tests://{module_name}/{file_path}')
def get_module_test(module_name: str, file_path: str):
    """Get a specific integration test file."""
    file_full_path = INTEG_TESTS_DIR / module_name / file_path
    
    if not file_full_path.exists() or not file_full_path.is_file():
        return f"Error: Integration test '{file_path}' not found for module '{module_name}'"
    
    # Read the file content
    with open(file_full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create and return a TextResource
    return TextResource(
        uri=f"cdk-api-integ-tests://{module_name}/{file_path}",
        name=file_path,
        text=content,
        description=f"Integration test: {file_path} for {module_name}",
        mime_type="text/markdown" if file_path.endswith(".md") else "text/plain"
    )


def main():
    """Run the MCP server with CLI argument support."""
    mcp.run()


if __name__ == '__main__':
    main()
