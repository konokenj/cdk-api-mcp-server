"""AWS CDK API MCP model definitions."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class FileItem(BaseModel):
    """File item model for CDK API documentation."""

    name: str = Field(description="Name of the file")
    uri: str = Field(description="URI of the file")
    is_directory: bool = Field(description="Whether the item is a directory")


class FileList(BaseModel):
    """List of files in CDK API documentation."""

    files: List[FileItem] = Field(default_factory=list, description="List of files")
    error: Optional[str] = Field(
        default=None, description="Error message if files not found"
    )
