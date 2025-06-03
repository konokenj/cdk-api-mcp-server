"""AWS CDK API MCP server implementation."""

import json
import mimetypes
import os
from typing import Optional

from fastmcp import FastMCP
from fastmcp.resources import TextResource
from pydantic import AnyUrl

from cdk_api_mcp_server.resources import (
    PackageResourceProvider,
    ResourceProvider,
    get_package_content,
)

# MIMEタイプの初期化と追加
mimetypes.init()
mimetypes.add_type("text/markdown", ".md")
mimetypes.add_type("text/typescript", ".ts")
mimetypes.add_type("application/json", ".json")

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
    @server.resource("cdk-api-docs://constructs/@aws-cdk", mime_type="application/json")
    def get_aws_cdk_alpha_packages():
        """List AWS CDK Alpha modules published in @aws-cdk namespace."""
        content = get_package_content(resource_provider, "@aws-cdk")

        # JSONとしてレスポンスを返す
        return TextResource(
            uri=AnyUrl.build(
                scheme="cdk-api-docs", host="constructs", path="/@aws-cdk"
            ),
            name="@aws-cdk",
            text=content,
            description="AWS CDK Alpha modules",
            mime_type="application/json",  # JSONレスポンスのMIMEタイプを設定
        )

    @server.resource(
        "cdk-api-docs://constructs/aws-cdk-lib", mime_type="application/json"
    )
    def get_aws_cdk_lib_packages():
        """List AWS CDK Stable modules in aws-cdk-lib package."""
        content = get_package_content(resource_provider, "aws-cdk-lib")

        # JSONとしてレスポンスを返す
        return TextResource(
            uri=AnyUrl.build(
                scheme="cdk-api-docs", host="constructs", path="/aws-cdk-lib"
            ),
            name="aws-cdk-lib",
            text=content,
            description="AWS CDK Stable modules",
            mime_type="application/json",  # JSONレスポンスのMIMEタイプを設定
        )

    # リソーステンプレート：パッケージ内のモジュール一覧
    @server.resource(
        "cdk-api-docs://constructs/{package_name}", mime_type="application/json"
    )
    def list_package_modules(package_name: str):
        """List all modules in the package."""
        modules = [
            item
            for item in resource_provider.list_resources(f"constructs/{package_name}")
            if resource_provider.resource_exists(f"constructs/{package_name}/{item}/")
        ]
        content = json.dumps(modules)

        # JSONとしてレスポンスを返す
        return TextResource(
            uri=AnyUrl.build(
                scheme="cdk-api-docs", host="constructs", path=f"/{package_name}/"
            ),
            name=f"{package_name}-modules",
            text=content,
            description=f"Modules in {package_name}",
            mime_type="application/json",  # JSONレスポンスのMIMEタイプを設定
        )

    # リソーステンプレート：モジュール内のファイル一覧
    @server.resource(
        "cdk-api-docs://constructs/{package_name}/{module_name}",
        mime_type="application/json",
    )
    def list_module_files(package_name: str, module_name: str):
        """List all files in the module."""
        files = resource_provider.list_resources(
            f"constructs/{package_name}/{module_name}"
        )
        content = json.dumps(files)

        # JSONとしてレスポンスを返す
        return TextResource(
            uri=AnyUrl.build(
                scheme="cdk-api-docs",
                host="constructs",
                path=f"/{package_name}/{module_name}/",
            ),
            name=f"{module_name}-files",
            text=content,
            description=f"Files in {package_name}/{module_name}",
            mime_type="application/json",  # JSONレスポンスのMIMEタイプを設定
        )

    # リソーステンプレート：すべてのファイルタイプ対応
    @server.resource(
        "cdk-api-docs://constructs/{package_name}/{module_name}/{file_name}"
    )
    def get_construct_file(package_name: str, module_name: str, file_name: str):
        """Get the file content."""
        resource_path = f"constructs/{package_name}/{module_name}/{file_name}"

        if not resource_provider.resource_exists(resource_path):
            error_message = f"Error: File '{resource_path}' not found"
            return TextResource(
                uri=AnyUrl.build(
                    scheme="cdk-api-docs",
                    host="constructs",
                    path=f"/{package_name}/{module_name}/{file_name}",
                ),
                name=file_name,
                text=error_message,
                description=f"Error: {resource_path}",
                mime_type="text/plain",
            )

        # リソースプロバイダーからコンテンツを取得
        content = resource_provider.get_resource_content(resource_path)

        # 拡張子に基づいてMIMEタイプを決定
        _, ext = os.path.splitext(file_name)

        # 特定の拡張子に対して明示的にMIMEタイプを設定
        if ext == ".md":
            mime_type = "text/markdown"
            description = f"Markdown file: {package_name}/{module_name}/{file_name}"
        elif ext == ".ts":
            mime_type = "text/typescript"
            description = f"TypeScript file: {package_name}/{module_name}/{file_name}"
        elif ext == ".json":
            mime_type = "application/json"
            description = f"JSON file: {package_name}/{module_name}/{file_name}"
        else:
            # その他の場合はmimetypesモジュールで判定
            mime_type, _ = mimetypes.guess_type(file_name)
            if mime_type is None:
                # デフォルトはプレーンテキスト
                mime_type = "text/plain"
            description = f"File: {package_name}/{module_name}/{file_name}"

        # Create and return a TextResource
        return TextResource(
            uri=AnyUrl.build(
                scheme="cdk-api-docs",
                host="constructs",
                path=f"/{package_name}/{module_name}/{file_name}",
            ),
            name=file_name,
            text=content,
            description=description,
            mime_type=mime_type,
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
