"""AWS CDK API MCP resource handlers."""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from importlib.resources import files
from pathlib import Path
from typing import List

# Set up logging
logger = logging.getLogger(__name__)


class ResourceProvider(ABC):
    """リソースプロバイダーのインターフェース"""

    @abstractmethod
    def get_resource_content(self, path: str) -> str:
        """リソースの内容を取得する"""

    @abstractmethod
    def list_resources(self, path: str) -> List[str]:
        """指定パスのリソース一覧を取得する"""

    @abstractmethod
    def resource_exists(self, path: str) -> bool:
        """リソースが存在するかチェックする"""


class PackageResourceProvider(ResourceProvider):
    """Pythonパッケージからリソースを提供するプロバイダー"""

    def __init__(self, package_name: str = "cdk_api_mcp_server"):
        self.package_name = package_name

    def get_resource_content(self, path: str) -> str:
        """新しいimportlib.resourcesのAPIを使用してパッケージからリソースを読み込む"""
        try:
            # 末尾のパス部分を分離（ディレクトリとファイル名）
            parts = path.strip("/").split("/")

            if len(parts) < 1:
                return "Error: Invalid resource path"

            # パスが"constructs"で始まる場合は"aws-cdk/constructs"に変換
            if parts[0] == "constructs":
                parts[0] = "aws-cdk/constructs"

            # resources配下の実際のファイルへのパスを構築
            base_path = files(self.package_name).joinpath("resources")

            # パス要素を結合
            resource_path = base_path
            for part in parts[0].split("/"):
                resource_path = resource_path.joinpath(part)

            for part in parts[1:]:
                resource_path = resource_path.joinpath(part)

            # ファイルとして存在するかチェック
            if resource_path.is_file():
                return resource_path.read_text(encoding="utf-8")
            elif resource_path.is_dir():
                # ディレクトリの場合は内容一覧を返す
                dir_contents = [entry.name for entry in resource_path.iterdir()]
                return f"Directory: {path}\nContents: {', '.join(sorted(dir_contents))}"
            else:
                return f"Error: Resource '{path}' not found"
        except (FileNotFoundError, IsADirectoryError, PermissionError) as e:
            logger.debug(f"リソースの取得に失敗: {path} - {e}")
            return f"Error: Resource '{path}' not found - {e!s}"

    def list_resources(self, path: str) -> List[str]:
        """新しいimportlib.resourcesのAPIを使用してパッケージ内のリソース一覧を取得する"""
        try:
            # resources配下の実際のディレクトリへのパスを構築
            base_path = files(self.package_name).joinpath("resources")

            # パス要素を結合
            resource_path = base_path
            if path:
                parts = path.strip("/").split("/")
                # パスが"constructs"で始まる場合は"aws-cdk/constructs"に変換
                if parts[0] == "constructs":
                    parts[0] = "aws-cdk/constructs"

                # パスの最初の部分（"aws-cdk/constructs"を含む）を分割して追加
                for part in parts[0].split("/"):
                    resource_path = resource_path.joinpath(part)

                # 残りのパス要素を追加
                for part in parts[1:]:
                    resource_path = resource_path.joinpath(part)

            # ディレクトリとして存在するかチェック
            if resource_path.is_dir():
                items = sorted([entry.name for entry in resource_path.iterdir()])

                # クライアントに返すときはハイフン形式に変換
                if path and path.startswith("constructs/") and not path.endswith("/"):
                    # ディレクトリでないパスの場合、モジュール名として扱いハイフン形式にする
                    return [item.replace("_", "-") for item in items]
                return items
            else:
                return []
        except (FileNotFoundError, NotADirectoryError, PermissionError) as e:
            logger.debug(f"リソース一覧の取得に失敗: {path} - {e}")
            return []

    def resource_exists(self, path: str) -> bool:
        """新しいimportlib.resourcesのAPIを使用してリソースが存在するかチェックする"""
        try:
            # resources配下の実際のファイルへのパスを構築
            base_path = files(self.package_name).joinpath("resources")

            # パス要素を結合
            resource_path = base_path
            if path:
                parts = path.strip("/").split("/")
                # パスが"constructs"で始まる場合は"aws-cdk/constructs"に変換
                if parts[0] == "constructs":
                    parts[0] = "aws-cdk/constructs"

                # パスの最初の部分（"aws-cdk/constructs"を含む）を分割して追加
                for part in parts[0].split("/"):
                    resource_path = resource_path.joinpath(part)

                # 残りのパス要素を追加
                for part in parts[1:]:
                    resource_path = resource_path.joinpath(part)

            # 存在チェック - Traversableには.exists()がないので、is_file()とis_dir()で確認
            return resource_path.is_file() or resource_path.is_dir()
        except (FileNotFoundError, PermissionError) as e:
            logger.debug(f"リソースの存在チェックに失敗: {path} - {e}")
            return False


# Define resource directories for backward compatibility with tests
CONSTRUCTS_DIR = Path(__file__).parent / "resources" / "aws-cdk" / "constructs"


def get_package_content(provider: ResourceProvider, package_name: str) -> str:
    """Get content for a package resource as a simple JSON array.

    Args:
        provider: Resource provider
        package_name: Package name

    Returns:
        JSON array of module names as a string
    """
    resource_path = f"constructs/{package_name}"

    if not provider.resource_exists(resource_path):
        return "[]"  # 空の配列を返す
    else:
        modules = provider.list_resources(resource_path)
        return json.dumps(modules)
