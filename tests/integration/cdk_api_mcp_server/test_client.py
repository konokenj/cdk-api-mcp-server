"""Integration tests for the CDK API MCP client."""
# mypy: disable-error-code="attr-defined"

import mimetypes

import pytest
from fastmcp import Client, FastMCP

from cdk_api_mcp_server.resources import PackageResourceProvider
from cdk_api_mcp_server.server import create_server


@pytest.fixture
def server():
    """Create a test server with PackageResourceProvider."""
    # MIMEタイプの初期化（テスト用）
    mimetypes.init()
    mimetypes.add_type("text/markdown", ".md")
    mimetypes.add_type("text/typescript", ".ts")
    mimetypes.add_type("application/json", ".json")

    # 実際のProviderインスタンスを作成
    provider = PackageResourceProvider()

    # server.pyのcreate_server関数を使ってサーバーを作成
    return create_server(provider)


@pytest.mark.asyncio
async def test_client_access_construct_path(server: FastMCP):
    """Test accessing construct path using MCP client."""
    # クライアントを作成
    client: Client = Client(server)

    # コンテキストマネージャでクライアント接続
    async with client:
        # aws-cdk-lib内のaws-s3のREADMEを取得
        resource_contents = await client.read_resource(
            "cdk-api-docs://constructs/aws-cdk-lib/aws-s3/README.md"
        )

        # リソースが取得できることを確認
        assert resource_contents is not None
        assert len(resource_contents) > 0

        # テキストリソースであることを確認（TextResourceContentsは型としてインポートできないためattr確認）
        assert hasattr(resource_contents[0], "text")

        # コンテンツを検証 - ヘッダーの存在のみ確認
        text = resource_contents[0].text
        assert isinstance(text, str)
        assert text.startswith("#")
        # MIMEタイプの検証 - テスト環境では text/plain になる場合がある
        assert resource_contents[0].mimeType in ["text/markdown", "text/plain"]


@pytest.mark.asyncio
async def test_client_direct_resource(server: FastMCP):
    """Test accessing direct resources using MCP client."""
    # クライアントを作成
    client: Client = Client(server)

    # コンテキストマネージャでクライアント接続
    async with client:
        # aws-cdk-libパッケージを取得（直接リソース）
        resource_contents = await client.read_resource(
            "cdk-api-docs://constructs/aws-cdk-lib"
        )

        # リソースが取得できることを確認
        assert resource_contents is not None
        assert len(resource_contents) > 0

        # テキストリソースであることを確認
        assert hasattr(resource_contents[0], "text")

        # コンテンツを検証 - シンプルなJSON配列として
        import json

        text = resource_contents[0].text
        assert isinstance(text, str)
        modules = json.loads(text)
        assert isinstance(modules, list)
        # 少なくとも1つのモジュールが存在することを確認
        assert len(modules) > 0
        # JSONレスポンスのMIMEタイプを検証
        assert resource_contents[0].mimeType == "application/json"


@pytest.mark.asyncio
async def test_client_alpha_resource(server: FastMCP):
    """Test accessing alpha package resource using MCP client."""
    # クライアントを作成
    client: Client = Client(server)

    # コンテキストマネージャでクライアント接続
    async with client:
        # @aws-cdkパッケージを取得（直接リソース）
        resource_contents = await client.read_resource(
            "cdk-api-docs://constructs/@aws-cdk"
        )

        # リソースが取得できることを確認
        assert resource_contents is not None
        assert len(resource_contents) > 0

        # テキストリソースであることを確認
        assert hasattr(resource_contents[0], "text")

        # コンテンツを検証 - シンプルなJSON配列として
        import json

        text = resource_contents[0].text
        assert isinstance(text, str)
        modules = json.loads(text)
        assert isinstance(modules, list)
        # 実際のファイルシステムにある任意のモジュール名を確認
        assert len(modules) > 0
        # 以下のいずれかが含まれていることを確認（実際のファイルシステムによって異なる可能性がある）
        assert any(
            name.startswith(("aws-", "app-", "custom-", "integ-", "cfnspec"))
            for name in modules
        )


@pytest.mark.asyncio
async def test_client_list_modules(server: FastMCP):
    """Test listing modules for aws-cdk-lib."""
    # クライアントを作成
    client: Client = Client(server)

    # コンテキストマネージャでクライアント接続
    async with client:
        # aws-cdk-libパッケージ内のモジュール一覧を取得
        resource_contents = await client.read_resource(
            "cdk-api-docs://constructs/aws-cdk-lib/"
        )

        # リソースが取得できることを確認
        assert resource_contents is not None
        assert len(resource_contents) > 0

        # テキストリソースであることを確認
        assert hasattr(resource_contents[0], "text")

        # JSONデータとして解析
        import json

        text = resource_contents[0].text
        assert isinstance(text, str)
        modules = json.loads(text)
        assert isinstance(modules, list)

        # 実際のファイルシステムにモジュールが存在することを確認
        assert len(modules) > 0


@pytest.mark.asyncio
async def test_client_list_module_files(server: FastMCP):
    """Test listing files within a specific module."""
    # クライアントを作成
    client: Client = Client(server)

    # コンテキストマネージャでクライアント接続
    async with client:
        # aws-cdk-lib/aws-s3モジュール内のファイル一覧を取得
        resource_contents = await client.read_resource(
            "cdk-api-docs://constructs/aws-cdk-lib/aws-s3/"
        )

        # リソースが取得できることを確認
        assert resource_contents is not None
        assert len(resource_contents) > 0

        # テキストリソースであることを確認
        assert hasattr(resource_contents[0], "text")

        # JSONデータとして解析
        import json

        text = resource_contents[0].text
        assert isinstance(text, str)
        files = json.loads(text)
        assert isinstance(files, list)

        # ファイルが少なくとも1つ存在することを確認
        assert len(files) > 0


@pytest.mark.asyncio
async def test_client_resource_not_found(server: FastMCP):
    """Test handling of non-existent resources."""
    # クライアントを作成
    client: Client = Client(server)

    # コンテキストマネージャでクライアント接続
    async with client:
        # 存在しないリソースへのアクセスで例外が発生することを確認
        import pytest
        from mcp.shared.exceptions import McpError

        with pytest.raises(McpError) as excinfo:
            await client.read_resource(
                "cdk-api-docs://constructs/non-existent-package/README.md"
            )

        # エラーメッセージが適切であることを確認
        assert "Unknown resource" in str(excinfo.value)
