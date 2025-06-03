"""Unit tests for the CDK API MCP server resources."""

from unittest.mock import patch

from cdk_api_mcp_server.resources import PackageResourceProvider


class TestPackageResourceProvider:
    """Test the PackageResourceProvider class with new path structure."""

    def test_get_resource_content_constructs_path(self):
        """Test getting resource content from constructs path structure."""
        # モックデータを設定
        mock_content = "# AWS S3\n\nThis is the README for AWS S3."

        provider = PackageResourceProvider()

        # 実際のREADME.mdはモックせず、実際のファイルから読み込まれる
        # 新しいパス構造でのリクエスト
        result = provider.get_resource_content(
            "constructs/aws-cdk-lib/aws-s3/README.md"
        )

        # 実際のファイルの内容を検証
        assert "# Amazon S3 Construct Library" in result

    def test_list_resources_constructs_path(self):
        """Test listing resources from constructs path structure."""
        provider = PackageResourceProvider()

        # 実際のファイルの一覧を取得
        result = provider.list_resources("constructs/aws-cdk-lib/aws-s3")

        # 少なくとも1つ以上のファイルがあることを確認
        assert len(result) > 0
        # README.mdが含まれているはず
        assert "README.md" in result

    def test_resource_exists_constructs_path(self):
        """Test checking if resource exists with constructs path structure."""
        provider = PackageResourceProvider()

        # ファイルの場合
        with patch("importlib.resources.is_resource", return_value=True):
            assert (
                provider.resource_exists("constructs/aws-cdk-lib/aws-s3/README.md")
                is True
            )

        # ディレクトリの場合
        with patch("importlib.resources.is_resource", return_value=False), patch(
            "importlib.resources.contents", return_value=["file1"]
        ):
            assert provider.resource_exists("constructs/aws-cdk-lib/aws-s3") is True

        # 存在しない場合
        with patch("importlib.resources.is_resource", return_value=False), patch(
            "importlib.resources.contents", side_effect=ModuleNotFoundError
        ):
            assert (
                provider.resource_exists("constructs/aws-cdk-lib/non-existent") is False
            )
