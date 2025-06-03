"""Integration tests for the CDK API MCP client."""

import pytest
from fastmcp import Client, FastMCP

from cdk_api_mcp_server.resources import MockResourceProvider
from cdk_api_mcp_server.server import create_server


@pytest.fixture
def server():
    """Create a test server with mock data."""
    # テスト用のリソースデータ（ファイルとディレクトリ）
    mock_data = {
        # aws-cdk-lib モジュール
        "constructs/aws-cdk-lib/": "Directory",
        # aws-s3 モジュール
        "constructs/aws-cdk-lib/aws-s3/": "Directory",
        "constructs/aws-cdk-lib/aws-s3/README.md": "# AWS S3\nThis is the README for AWS S3.",
        "constructs/aws-cdk-lib/aws-s3/index.ts": "export * from './lib';",
        # aws-lambda モジュール
        "constructs/aws-cdk-lib/aws-lambda/": "Directory",
        "constructs/aws-cdk-lib/aws-lambda/README.md": "# AWS Lambda\nThis is a readme for Lambda.",
        # aws-dynamodb モジュール
        "constructs/aws-cdk-lib/aws-dynamodb/": "Directory",
        "constructs/aws-cdk-lib/aws-dynamodb/README.md": "# DynamoDB\nThis is a readme for DynamoDB.",
        # @aws-cdk モジュール
        "constructs/@aws-cdk/": "Directory",
        "constructs/@aws-cdk/aws-apigateway/": "Directory",
        "constructs/@aws-cdk/aws-apigateway/README.md": "# API Gateway\nThis is a readme for API Gateway.",
    }

    # モックリソースプロバイダー
    provider = MockResourceProvider(mock_data)

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

        # コンテンツを検証
        assert "# AWS S3" in resource_contents[0].text
        assert "This is the README for AWS S3." in resource_contents[0].text


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

        # コンテンツを検証
        assert "aws-cdk-lib" in resource_contents[0].text
        assert "Available Modules" in resource_contents[0].text


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

        # コンテンツを検証
        assert "@aws-cdk" in resource_contents[0].text
        assert "Available Modules" in resource_contents[0].text


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

        # JSONデータとして解析
        content = resource_contents[0].text
        if content:
            import json

            data = json.loads(content)
            files = data.get("files", [])

            # サンプルデータには少なくとも「aws-s3」、「aws-lambda」、「aws-dynamodb」が含まれているはず
            file_names = {file["name"] for file in files}

            assert "aws-s3" in file_names
            assert "aws-lambda" in file_names
            assert "aws-dynamodb" in file_names


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

        # JSONデータとして解析
        content = resource_contents[0].text
        if content:
            import json

            data = json.loads(content)
            files = data.get("files", [])

            # モジュール内のファイル一覧にはREADME.mdとindex.tsが含まれているはず
            file_names = {file["name"] for file in files}

            assert "README.md" in file_names
            assert "index.ts" in file_names


@pytest.mark.asyncio
async def test_client_apigateway_module(server: FastMCP):
    """Test accessing @aws-cdk module resources."""
    # クライアントを作成
    client: Client = Client(server)

    # コンテキストマネージャでクライアント接続
    async with client:
        # @aws-cdk/aws-apigatewayのREADMEを取得
        resource_contents = await client.read_resource(
            "cdk-api-docs://constructs/@aws-cdk/aws-apigateway/README.md"
        )

        # リソースが取得できることを確認
        assert resource_contents is not None
        assert len(resource_contents) > 0

        # コンテンツを検証
        assert "# API Gateway" in resource_contents[0].text
        assert "This is a readme for API Gateway." in resource_contents[0].text
