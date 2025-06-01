"""Tests for the CDK API MCP server."""

import pytest
from cdk_api_mcp_server.core.server import main, mcp
from unittest.mock import patch


def test_mcp_server_initialization():
    """Test MCP server initialization."""
    # Check server name
    assert mcp.name == 'AWS CDK API MCP Server'
    
    # Check dependencies
    assert len(mcp.dependencies) == 0  # Currently no dependencies


@pytest.mark.asyncio
async def test_mcp_server_resource_registration():
    """Test MCP server resource registration."""
    # Get all registered resources
    resources = await mcp.list_resources()
    
    # Check CDK API resources
    assert any(r.uri_template == 'cdk-api-docs://' for r in resources)
    assert any(r.uri_template == 'cdk-api-docs://root/' for r in resources)
    assert any(r.uri_template == 'cdk-api-docs://root/{file_name}' for r in resources)
    assert any(r.uri_template == 'cdk-api-docs://packages/' for r in resources)
    assert any(r.uri_template == 'cdk-api-docs://packages/{package_name}/' for r in resources)
    assert any(r.uri_template == 'cdk-api-docs://packages/{package_name}/{module_name}/' for r in resources)
    assert any(r.uri_template == 'cdk-api-docs://packages/{package_name}/{module_name}/{file_path}' for r in resources)
    
    # Check integration tests resources
    assert any(r.uri_template == 'cdk-api-integ-tests://' for r in resources)
    assert any(r.uri_template == 'cdk-api-integ-tests://{module_name}/' for r in resources)
    assert any(r.uri_template == 'cdk-api-integ-tests://{module_name}/{file_path}' for r in resources)


@patch('cdk_api_mcp_server.core.server.mcp.run')
def test_main_with_default_args(mock_run):
    """Test main function with default arguments."""
    with patch('sys.argv', ['server.py']):
        main()
        mock_run.assert_called_once_with()
