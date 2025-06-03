"""Unit tests for the CDK API MCP server."""

from unittest.mock import MagicMock, patch

from fastmcp import FastMCP

from cdk_api_mcp_server.server import main


def test_main_runs_server():
    """main関数がMCPサーバーのrun()を呼び出すことをテスト"""
    # モックサーバーインスタンスを作成
    mock_mcp = MagicMock(spec=FastMCP)

    # グローバルな mcp 変数をモック
    with patch("cdk_api_mcp_server.server.mcp", mock_mcp):
        # run()メソッドをモック
        mock_mcp.run = MagicMock()

        # main関数を実行
        main()

        # runメソッドが呼ばれたことを確認
        mock_mcp.run.assert_called_once()
