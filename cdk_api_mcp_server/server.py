"""AWS CDK API MCP server implementation."""

import json
from typing import Optional

from fastmcp import FastMCP
from fastmcp.resources import TextResource
from pydantic import AnyUrl

from cdk_api_mcp_server.resources import (
    PackageResourceProvider,
    ResourceProvider,
    get_package_content,
)

# デフォルトのMCPサーバーインスタンス
mcp: FastMCP = FastMCP()
# デフォルトのリソースプロバイダー
_default_provider = PackageResourceProvider()


def create_server(provider: Optional[ResourceProvider] = None) -> FastMCP:
    """Create an MCP server with the given resource provider.

    Args:
        provider: ResourceProvider for CDK API resources. Defaults to PackageResourceProvider.

    Returns:
        FastMCP server instance with registered resources
    """
    # 使用するリソースプロバイダー
    resource_provider = provider or _default_provider

    # 新しいサーバーインスタンスを作成
    server: FastMCP = FastMCP()

    # nameフィールドにアクセスする方法は提供されていないため、descriptionを使う
    server.description = "AWS CDK API MCP Server"

    # 定義済みのパッケージとして直接リソース登録
    @server.resource("cdk-api-docs://constructs/@aws-cdk")
    def get_aws_cdk_alpha_packages():
        """Get AWS CDK Alpha modules published in @aws-cdk namespace."""
        return get_package_content(resource_provider, "@aws-cdk")

    @server.resource("cdk-api-docs://constructs/aws-cdk-lib")
    def get_aws_cdk_lib_packages():
        """Get AWS CDK Stable modules in aws-cdk-lib package."""
        return get_package_content(resource_provider, "aws-cdk-lib")

    # リソーステンプレート：パッケージ内のモジュール一覧
    @server.resource("cdk-api-docs://constructs/{package_name}/")
    def list_package_modules(package_name: str):
        """List all modules in a package."""
        modules = [
            item
            for item in resource_provider.list_resources(f"constructs/{package_name}")
            if resource_provider.resource_exists(f"constructs/{package_name}/{item}/")
        ]
        return json.dumps(modules)

    # リソーステンプレート：モジュール内のファイル一覧
    @server.resource("cdk-api-docs://constructs/{package_name}/{module_name}/")
    def list_module_files(package_name: str, module_name: str):
        """List all files in a module."""
        files = resource_provider.list_resources(
            f"constructs/{package_name}/{module_name}"
        )
        return json.dumps(files)

    # リソーステンプレート：ファイルの内容を読み込む
    @server.resource(
        "cdk-api-docs://constructs/{package_name}/{module_name}/{file_name}"
    )
    def get_construct_file(package_name: str, module_name: str, file_name: str):
        """Get a file from the constructs directory."""
        resource_path = f"constructs/{package_name}/{module_name}/{file_name}"

        if not resource_provider.resource_exists(resource_path):
            return f"Error: File '{resource_path}' not found"

        # リソースプロバイダーからコンテンツを取得
        content = resource_provider.get_resource_content(resource_path)

        # Create and return a TextResource
        return TextResource(
            uri=AnyUrl.build(
                scheme="cdk-api-docs",
                host="constructs",
                path=f"/{package_name}/{module_name}/{file_name}",
            ),
            name=file_name,
            text=content,
            description=f"Construct file: {package_name}/{module_name}/{file_name}",
            mime_type="text/markdown" if file_name.endswith(".md") else "text/plain",
        )

    return server


# デフォルトのサーバーを初期化
def initialize_default_server() -> None:
    """Initialize the default MCP server with resources."""
    global mcp
    default_server = create_server(_default_provider)
    # 以前のmcpの属性を新しいサーバーにコピー
    mcp.__dict__.update(default_server.__dict__)


# デフォルトサーバーを初期化
initialize_default_server()


def main():
    """Run the MCP server."""
    import logging

    logging.basicConfig(level=logging.INFO)
    # サーバーを実行
    mcp.run()


if __name__ == "__main__":
    main()
