"""Unit tests for the CDK API MCP server resources."""

from unittest.mock import patch

from cdk_api_mcp_server.core.resources import (
    MockResourceProvider,
    PackageResourceProvider,
)


class TestPackageResourceProvider:
    """Test the PackageResourceProvider class with new path structure."""

    def test_get_resource_content_constructs_path(self):
        """Test getting resource content from constructs path structure."""
        # モックデータを設定
        mock_content = "# AWS S3\n\nThis is the README for AWS S3."

        provider = PackageResourceProvider()

        # importlib.resources.is_resourceとread_textをモック
        with patch("importlib.resources.is_resource", return_value=True), patch(
            "importlib.resources.read_text", return_value=mock_content
        ):
            # 新しいパス構造でのリクエスト
            result = provider.get_resource_content(
                "constructs/aws-cdk-lib/aws-s3/README.md"
            )

            assert result == mock_content

    def test_list_resources_constructs_path(self):
        """Test listing resources from constructs path structure."""
        # モックデータを設定
        mock_resources = ["README.md", "index.ts", "lib"]

        provider = PackageResourceProvider()

        # importlib.resources.contentsをモック
        with patch("importlib.resources.contents", return_value=mock_resources):
            # 新しいパス構造でのリクエスト
            result = provider.list_resources("constructs/aws-cdk-lib/aws-s3")

            assert sorted(result) == sorted(mock_resources)

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


class TestMockResourceProvider:
    """Test the MockResourceProvider class with new path structure."""

    def test_get_resource_content(self):
        """Test getting resource content."""
        # モックデータを設定
        mock_data = {
            "constructs/aws-cdk-lib/aws-s3/README.md": "# AWS S3\nThis is a readme",
            "constructs/@aws-cdk/aws-apigateway/README.md": "# API Gateway\nThis is a readme",
        }

        provider = MockResourceProvider(mock_data)

        # 正常系テスト
        assert (
            provider.get_resource_content("constructs/aws-cdk-lib/aws-s3/README.md")
            == mock_data["constructs/aws-cdk-lib/aws-s3/README.md"]
        )
        assert (
            provider.get_resource_content(
                "constructs/@aws-cdk/aws-apigateway/README.md"
            )
            == mock_data["constructs/@aws-cdk/aws-apigateway/README.md"]
        )

        # ディレクトリ内容の取得テスト
        mock_data_with_dir = {
            "constructs/aws-cdk-lib/aws-s3/README.md": "# AWS S3\nThis is a readme",
            "constructs/aws-cdk-lib/aws-s3/index.md": "Index file",
        }
        provider_with_dir = MockResourceProvider(mock_data_with_dir)

        dir_result = provider_with_dir.get_resource_content(
            "constructs/aws-cdk-lib/aws-s3"
        )
        assert "Directory:" in dir_result
        assert "README.md" in dir_result
        assert "index.md" in dir_result

        # 存在しないリソース
        not_found = provider.get_resource_content(
            "constructs/aws-cdk-lib/non-existent/README.md"
        )
        assert "Error:" in not_found
        assert "not found" in not_found

    def test_list_resources(self):
        """Test listing resources."""
        # モックデータを設定
        mock_data = {
            "constructs/aws-cdk-lib/aws-s3/README.md": "# AWS S3\nThis is a readme",
            "constructs/aws-cdk-lib/aws-s3/index.md": "Index file",
            "constructs/aws-cdk-lib/aws-lambda/README.md": "# AWS Lambda\nThis is a readme",
            "constructs/@aws-cdk/aws-apigateway/README.md": "# API Gateway\nThis is a readme",
        }

        provider = MockResourceProvider(mock_data)

        # ルートディレクトリ
        root_resources = provider.list_resources("")
        assert sorted(root_resources) == ["constructs"]

        # constructsディレクトリ
        constructs_resources = provider.list_resources("constructs")
        assert sorted(constructs_resources) == ["@aws-cdk", "aws-cdk-lib"]

        # aws-cdk-libディレクトリ
        aws_cdk_lib_resources = provider.list_resources("constructs/aws-cdk-lib")
        assert sorted(aws_cdk_lib_resources) == ["aws-lambda", "aws-s3"]

        # aws-s3ディレクトリ
        aws_s3_resources = provider.list_resources("constructs/aws-cdk-lib/aws-s3")
        assert sorted(aws_s3_resources) == ["README.md", "index.md"]

        # 存在しないディレクトリ
        non_existent_resources = provider.list_resources(
            "constructs/aws-cdk-lib/non-existent"
        )
        assert non_existent_resources == []

    def test_resource_exists(self):
        """Test checking if resource exists."""
        # モックデータを設定
        mock_data = {
            "constructs/aws-cdk-lib/aws-s3/README.md": "# AWS S3\nThis is a readme",
            "constructs/aws-cdk-lib/aws-lambda/README.md": "# AWS Lambda\nThis is a readme",
        }

        provider = MockResourceProvider(mock_data)

        # 存在するリソース
        assert (
            provider.resource_exists("constructs/aws-cdk-lib/aws-s3/README.md") is True
        )

        # 存在するディレクトリ
        assert provider.resource_exists("constructs/aws-cdk-lib/aws-s3") is True
        assert provider.resource_exists("constructs/aws-cdk-lib") is True
        assert provider.resource_exists("constructs") is True

        # 存在しないリソース
        assert (
            provider.resource_exists("constructs/aws-cdk-lib/non-existent/README.md")
            is False
        )
        assert provider.resource_exists("constructs/aws-cdk-lib/non-existent") is False
