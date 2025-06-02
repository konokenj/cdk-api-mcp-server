"""Tests for the CDK API MCP server."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cdk_api_mcp_server.core.resources import MockResourceProvider
from cdk_api_mcp_server.core.server import CDKApiServer, main

# modelmcpがインストールされているかチェック
HAS_MODELMCP = False
try:
    from modelmcp.client import MCPClient

    HAS_MODELMCP = True
except ImportError:
    # modelmcpがない場合はスキップ
    pass


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


@patch("cdk_api_mcp_server.core.server.FastMCP")
@pytest.mark.asyncio  # 非同期テストとしてマーク
async def test_server_with_mock_resources(mock_fastmcp_class):
    """モックリソースを使用したサーバーのテスト"""
    # サーバー応答のモックデータ
    root_category_response = json.dumps(
        {
            "categories": [
                {
                    "name": "root",
                    "uri": "cdk-api-docs://root/",
                    "description": "Root level documentation files",
                    "is_directory": True,
                },
                {
                    "name": "packages",
                    "uri": "cdk-api-docs://packages/",
                    "description": "AWS CDK packages documentation",
                    "is_directory": True,
                },
            ]
        }
    )

    files_response = json.dumps(
        {
            "files": [
                {
                    "name": "README.md",
                    "uri": "cdk-api-docs://root/README.md",
                    "is_directory": False,
                },
                {
                    "name": "GUIDE.md",
                    "uri": "cdk-api-docs://root/GUIDE.md",
                    "is_directory": False,
                },
            ]
        }
    )

    # FastMCPのモック設定
    mock_fastmcp_instance = MagicMock()
    mock_fastmcp_class.return_value = mock_fastmcp_instance

    # リソースハンドラーのモック
    mock_root_category_handler = AsyncMock(return_value=root_category_response)
    mock_files_handler = MagicMock(return_value=files_response)

    # モックリソーステンプレート
    mock_templates = {
        "cdk-api-docs://": mock_root_category_handler,
        "cdk-api-docs://root/": mock_files_handler,
    }

    # get_resource_templates()のモック
    async def mock_get_templates():
        return mock_templates

    mock_fastmcp_instance.get_resource_templates = mock_get_templates

    # テスト用のモックデータを設定
    mock_data = {
        "aws-cdk/docs/README.md": "# AWS CDK Documentation\nTest content",
        "aws-cdk/docs/GUIDE.md": "# CDK Guide\nGuide content",
        "aws-cdk/docs/packages/aws-lambda/README.md": "# AWS Lambda\nLambda content",
    }
    mock_provider = MockResourceProvider(mock_data)

    # サーバーインスタンスを作成
    server = CDKApiServer(resource_provider=mock_provider)

    # リソーステンプレートを取得 (awaitを使用)
    resource_templates = await server.mcp.get_resource_templates()

    # cdk-api-docs:// リソースのレスポンスをテスト
    resource_handler = resource_templates.get("cdk-api-docs://")
    assert resource_handler is not None

    # リソースハンドラを実行 (awaitを使用)
    response = await resource_handler()
    data = json.loads(response)

    # カテゴリが正しく含まれているかチェック
    assert "categories" in data
    assert len(data["categories"]) > 0
    assert any(cat["name"] == "root" for cat in data["categories"])

    # ファイルリストのレスポンスをテスト
    resource_handler = resource_templates.get("cdk-api-docs://root/")
    assert resource_handler is not None

    # ファイルリストハンドラを実行 (同期関数の場合はそのまま実行)
    response = resource_handler()
    data = json.loads(response)

    # ファイルリストが正しく含まれているかチェック
    assert "files" in data
    file_names = [file["name"] for file in data["files"]]
    assert "README.md" in file_names
    assert "GUIDE.md" in file_names

    # モックが呼び出されたことを確認
    mock_root_category_handler.assert_called_once()
    mock_files_handler.assert_called_once()


@pytest.fixture
def mock_server():
    """サーバーのモックフィクスチャ"""
    server = MagicMock()
    return server


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


# modelmcpがインストールされている場合のみテスト実行
if HAS_MODELMCP:

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True, reason="For local development only, requires running server"
    )
    async def test_with_real_mcp_client():
        """実際のMCPクライアントを使用した統合テスト

        このテストはローカル開発用であり、実行中のサーバーが必要です。
        CI環境では自動的にスキップされます。
        """
        # サーバーが別プロセスで実行されていることを前提
        client = MCPClient()

        # ローカルホストのMCPサーバーに接続
        await client.connect("tcp://localhost:8080")

        try:
            # ルートカテゴリのリソースにアクセス
            resource = await client.access_resource("cdk-api-docs://")
            data = json.loads(resource)

            assert "categories" in data
            assert len(data["categories"]) > 0

        finally:
            # クライアントをクローズ
            await client.close()
