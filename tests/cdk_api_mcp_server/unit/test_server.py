"""Unit tests for the CDK API MCP server."""

from unittest.mock import MagicMock, patch

from cdk_api_mcp_server.core.resources import MockResourceProvider
from cdk_api_mcp_server.core.server import CDKApiServer, main


def test_cdk_api_server_initialization():
    """CDKApiServerの初期化をテスト"""
    # モックリソースプロバイダーを作成
    mock_provider = MockResourceProvider()

    # サーバーを初期化
    server = CDKApiServer(resource_provider=mock_provider)

    # サーバー名をチェック
    assert server.mcp.name == "AWS CDK API MCP Server"

    # 依存関係をチェック
    assert len(server.mcp.dependencies) == 0

    # リソースプロバイダーが正しく設定されているか
    assert server.resource_provider == mock_provider


@patch("cdk_api_mcp_server.core.server.CDKApiServer")
def test_main_creates_and_runs_server(mock_server_class):
    """main関数がCDKApiServerを作成して実行することをテスト"""
    # モックサーバーインスタンス
    mock_server_instance = MagicMock()
    mock_server_class.return_value = mock_server_instance

    # main関数を実行
    main()

    # サーバーが作成されたことを確認
    mock_server_class.assert_called_once()

    # runメソッドが呼ばれたことを確認
    mock_server_instance.run.assert_called_once()
