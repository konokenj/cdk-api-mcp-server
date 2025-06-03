"""Tests for the CDK API MCP server resources."""

from unittest.mock import patch

from cdk_api_mcp_server.resources import PackageResourceProvider


def test_package_resource_provider_get_content():
    """Test retrieving content from the package provider."""
    provider = PackageResourceProvider()

    # ファイル内容の取得テスト - 実際のファイルを使用
    result = provider.get_resource_content("constructs/aws-cdk-lib/aws-s3/README.md")
    assert "# Amazon S3 Construct Library" in result

    # 存在しないファイル取得テスト
    result = provider.get_resource_content(
        "constructs/aws-cdk-lib/aws-s3/nonexistent.md"
    )
    assert "Error: Resource" in result
    assert "not found" in result


def test_package_resource_provider_list_resources():
    """Test listing resources from the package provider."""
    provider = PackageResourceProvider()

    # リソース一覧取得テスト - 実際のファイルを使用
    result = provider.list_resources("constructs/aws-cdk-lib/aws-s3")
    assert (
        "README.md" in result
    )  # 実際のファイルシステムにはREADME.mdが含まれているはず


@patch("importlib.resources.contents")
@patch("importlib.resources.is_resource")
def test_package_resource_provider_resource_exists(mock_is_resource, mock_contents):
    """Test checking if resources exist in the package provider."""
    # モックの設定
    mock_contents.return_value = ["README.md", "examples"]
    mock_is_resource.return_value = True

    provider = PackageResourceProvider()

    # 存在するディレクトリのチェック
    mock_contents.side_effect = None
    assert provider.resource_exists("constructs/aws-cdk-lib/aws-s3") is True

    # 存在するファイルのチェック
    assert provider.resource_exists("constructs/aws-cdk-lib/aws-s3/README.md") is True

    # 存在しないパスのチェック
    mock_contents.side_effect = ModuleNotFoundError("Module not found")
    mock_is_resource.return_value = False
    assert provider.resource_exists("constructs/nonexistent") is False


def test_package_resource_provider_directory_content():
    """Test retrieving directory content from the package provider."""
    provider = PackageResourceProvider()

    # ディレクトリ内容の取得テスト - ディレクトリパスとして扱う - 実際のファイルシステムを使用
    result = provider.get_resource_content("constructs/aws-cdk-lib/aws-s3")
    assert "Directory" in result
    assert (
        "README.md" in result
    )  # 実際のファイルシステムにはREADME.mdが含まれているはず
