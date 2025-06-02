#!/usr/bin/env python3
"""AWS CDK API MCP server implementation."""

import logging
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
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


class Category(BaseModel):
    """Category model for CDK API documentation."""
    
    name: str = Field(description="Name of the category")
    uri: str = Field(description="URI of the category")
    description: str = Field(description="Description of the category")
    is_directory: bool = Field(default=True, description="Whether the category is a directory")


class CategoryList(BaseModel):
    """List of categories in CDK API documentation."""
    
    categories: List[Category] = Field(default_factory=list, description="List of categories")
    error: Optional[str] = Field(default=None, description="Error message if categories not found")


# Register resource templates for hierarchical navigation
@mcp.resource('cdk-api-docs://')
async def list_root_categories():
    """List all available categories in the CDK API documentation."""
    if not DOCS_DIR.exists():
        return json.dumps(CategoryList(error="Documentation directory not found").model_dump())
    
    categories = []
    # Add root category
    categories.append(Category(
        name="root",
        uri="cdk-api-docs://root/",
        description="Root level documentation files",
        is_directory=True
    ))
    
    # Add packages category if it exists
    packages_dir = DOCS_DIR / "packages"
    if packages_dir.exists() and packages_dir.is_dir():
        categories.append(Category(
            name="packages",
            uri="cdk-api-docs://packages/",
            description="AWS CDK packages documentation",
            is_directory=True
        ))
    
    return json.dumps(CategoryList(categories=categories).model_dump())


class FileItem(BaseModel):
    """File item model for CDK API documentation."""
    
    name: str = Field(description="Name of the file")
    uri: str = Field(description="URI of the file")
    is_directory: bool = Field(description="Whether the item is a directory")


class FileList(BaseModel):
    """List of files in CDK API documentation."""
    
    files: List[FileItem] = Field(default_factory=list, description="List of files")
    error: Optional[str] = Field(default=None, description="Error message if files not found")


@mcp.resource('cdk-api-docs://root/')
def list_root_files():
    """List all files in the root directory of the CDK API documentation."""
    if not DOCS_DIR.exists():
        return json.dumps(FileList(error="Documentation directory not found").model_dump())
    
    files = []
    for item in DOCS_DIR.iterdir():
        if item.is_file():
            files.append(FileItem(
                name=item.name,
                uri=f"cdk-api-docs://root/{item.name}",
                is_directory=False
            ))
        elif item.is_dir() and item.name != "packages":  # Skip packages dir as it's handled separately
            files.append(FileItem(
                name=item.name,
                uri=f"cdk-api-docs://root/{item.name}/",
                is_directory=True
            ))
    
    return json.dumps(FileList(files=files).model_dump())


class RootFile(BaseModel):
    """Root file parameters for CDK API documentation."""
    
    file_name: str = Field(description="Name of the file")


@mcp.resource('cdk-api-docs://root/{file_name}')
def get_root_file(file_name: str):
    """Get a file from the root directory of the CDK API documentation."""
    params = RootFile(file_name=file_name)
    file_path = DOCS_DIR / params.file_name
    
    if not file_path.exists() or not file_path.is_file():
        return f"Error: File '{params.file_name}' not found"
    
    # Read the file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create and return a TextResource
    return TextResource(
        uri=f"cdk-api-docs://root/{params.file_name}",
        name=params.file_name,
        text=content,
        description=f"Root documentation file: {params.file_name}",
        mime_type="text/markdown" if params.file_name.endswith(".md") else "text/plain"
    )
