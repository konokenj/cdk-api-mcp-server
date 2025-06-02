#!/usr/bin/env python3
"""AWS CDK API MCP resource handlers."""

import logging
import importlib.resources
import os
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field


# Set up logging
logger = logging.getLogger(__name__)


# Resource package paths
DOCS_PACKAGE = "cdk_api_mcp_server.resources.aws-cdk.docs"
INTEG_TESTS_PACKAGE = "cdk_api_mcp_server.resources.aws-cdk.integ-tests"

# Define resource directories for backward compatibility with tests
DOCS_DIR = Path(__file__).parent.parent / "resources" / "aws-cdk" / "docs"
INTEG_TESTS_DIR = Path(__file__).parent.parent / "resources" / "aws-cdk" / "integ-tests"


class ResourcePath(BaseModel):
    """Resource path model for importlib.resources."""
    
    package_path: str = Field(description="Base package path")
    parts: List[str] = Field(default_factory=list, description="Additional path parts")
    
    def get_full_path(self) -> str:
        """Get the full package path by joining parts."""
        return ".".join([self.package_path] + self.parts)


def get_resource_path(package_path: str, *parts: str) -> str:
    """Get a resource path for importlib.resources.

    Args:
        package_path: Base package path
        *parts: Additional path parts to join

    Returns:
        Full package path
    """
    resource_path = ResourcePath(package_path=package_path, parts=list(parts))
    return resource_path.get_full_path()


def is_resource_dir(package_path: str) -> bool:
    """Check if a resource path is a directory.

    Args:
        package_path: Package path to check

    Returns:
        True if the path is a directory, False otherwise
    """
    try:
        # Try to get a list of resources in the package
        resources = list(importlib.resources.contents(package_path))
        return len(resources) > 0
    except (ModuleNotFoundError, ImportError):
        return False


def list_resources(package_path: str) -> List[str]:
    """List resources in a package.

    Args:
        package_path: Package path to list resources from

    Returns:
        List of resource names
    """
    try:
        return sorted(list(importlib.resources.contents(package_path)))
    except (ModuleNotFoundError, ImportError):
        return []


def is_resource_file(package_path: str, name: str) -> bool:
    """Check if a resource is a file.

    Args:
        package_path: Package path
        name: Resource name

    Returns:
        True if the resource is a file, False otherwise
    """
    try:
        return importlib.resources.is_resource(package_path, name)
    except (ModuleNotFoundError, ImportError):
        return False


class ResourceContent(BaseModel):
    """Resource content model."""
    
    content: str = Field(description="Content of the resource")
    error: Optional[str] = Field(default=None, description="Error message if resource not found")


def read_resource_text(package_path: str, name: str) -> str:
    """Read text from a resource.

    Args:
        package_path: Package path
        name: Resource name

    Returns:
        Resource content as text
    """
    try:
        content = importlib.resources.read_text(package_path, name)
        return content
    except (ModuleNotFoundError, ImportError, FileNotFoundError):
        error_msg = f"Error: Resource '{name}' not found in '{package_path}'"
        logger.error(error_msg)
        return error_msg
