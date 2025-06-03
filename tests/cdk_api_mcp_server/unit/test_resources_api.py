"""Tests for the CDK API MCP server resources."""

from unittest.mock import mock_open, patch

import pytest

from cdk_api_mcp_server.core.resources import get_cdk_api_docs, get_cdk_api_integ_tests


@pytest.mark.asyncio
async def test_get_cdk_api_docs_file():
    """Test getting a documentation file."""
    mock_content = "# AWS S3\n\nThis is the README for AWS S3."

    with patch("os.path.exists", return_value=True), patch(
        "os.path.isdir", return_value=False
    ), patch("builtins.open", mock_open(read_data=mock_content)):
        result = await get_cdk_api_docs(
            "packages", "aws-cdk-lib", "aws-s3", "README.md"
        )

        assert result == mock_content


@pytest.mark.asyncio
async def test_get_cdk_api_docs_directory():
    """Test getting a directory listing."""
    with patch("os.path.exists", return_value=True), patch(
        "os.path.isdir", return_value=True
    ), patch("os.listdir", return_value=["README.md", "examples", "index.md"]):
        result = await get_cdk_api_docs("packages", "aws-cdk-lib", "aws-s3", "")

        assert "# Contents of aws-cdk-lib/aws-s3" in result
        assert "README.md" in result
        assert "examples/" in result
        assert "index.md" in result


@pytest.mark.asyncio
async def test_get_cdk_api_docs_not_found():
    """Test getting a file that doesn't exist."""
    with patch("os.path.exists", return_value=False):
        result = await get_cdk_api_docs(
            "packages", "aws-cdk-lib", "aws-s3", "nonexistent.md"
        )

        assert "Error: File" in result
        assert "not found" in result


@pytest.mark.asyncio
async def test_get_cdk_api_docs_other_category():
    """Test getting a file from another category."""
    mock_content = "# Custom Category\n\nThis is a custom category file."

    with patch("os.path.exists", return_value=True), patch(
        "os.path.isdir", return_value=False
    ), patch("builtins.open", mock_open(read_data=mock_content)):
        result = await get_cdk_api_docs("custom", "section", "topic", "file.md")

        assert result == mock_content


@pytest.mark.asyncio
async def test_get_cdk_api_integ_tests_file():
    """Test getting an integration test file."""
    mock_content = "console.log('test');"

    with patch("os.path.exists", return_value=True), patch(
        "os.path.isdir", return_value=False
    ), patch("builtins.open", mock_open(read_data=mock_content)):
        result = await get_cdk_api_integ_tests("aws-s3", "integ.test1.ts")

        assert result == mock_content


@pytest.mark.asyncio
async def test_get_cdk_api_integ_tests_directory():
    """Test getting a directory listing for integration tests."""
    with patch("os.path.exists", return_value=True), patch(
        "os.path.isdir", return_value=True
    ), patch("os.listdir", return_value=["integ.test1.ts", "integ.test2.ts"]):
        result = await get_cdk_api_integ_tests("aws-s3", "")

        assert "# Integration Tests for aws-s3" in result
        assert "integ.test1.ts" in result
        assert "integ.test2.ts" in result


@pytest.mark.asyncio
async def test_get_cdk_api_integ_tests_not_found():
    """Test getting an integration test file that doesn't exist."""
    with patch("os.path.exists", return_value=False):
        result = await get_cdk_api_integ_tests("aws-s3", "nonexistent.md")

        assert "Error: File" in result
        assert "not found" in result


@pytest.mark.asyncio
async def test_get_cdk_api_integ_tests_no_file_path():
    """Test getting integration tests with no file path."""
    with patch("os.path.exists", return_value=True), patch(
        "os.path.isdir", return_value=True
    ), patch("os.listdir", return_value=["integ.test1.ts", "integ.test2.ts", "subdir"]):
        result = await get_cdk_api_integ_tests("aws-s3")

        assert "# Integration Tests for aws-s3" in result
        assert "integ.test1.ts" in result
        assert "integ.test2.ts" in result
        assert "subdir/" in result
