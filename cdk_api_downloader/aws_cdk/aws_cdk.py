import glob
import logging
import os
import re

# ロガーの設定
logger = logging.getLogger(__name__)


def find_markdown_files(basedir: str):
    """
    Find markdown files in $basedir.
    Include:
        - packages/@aws-cdk/**/*.md
        - packages/aws-cdk-lib/**/*.md
    Exclude:
        - cli-regression-patches/
        - *.snapshot/
        - Files containing 'There are no hand-written'

    Args:
        basedir (str): base directory of the repository
    """
    # 特定のパターンに一致するファイルを検索
    patterns = [
        f"{basedir}/packages/@aws-cdk/**/*.md",
        f"{basedir}/packages/aws-cdk-lib/**/*.md",
    ]

    for pattern in patterns:
        for file in glob.glob(pattern, recursive=True):
            # 除外条件をチェック
            if "cli-regression-patches/" in file or ".snapshot/" in file:
                continue

            # ファイルの内容をチェック
            try:
                with open(file, encoding="utf-8") as f:
                    content = f.read()
                    if "There are no hand-written" in content:
                        continue
            except (OSError, UnicodeDecodeError) as e:
                # ファイル読み込みエラーの場合はスキップ
                logger.warning("Failed to read file %s: %s", file, e)
                continue

            yield file


def find_integ_test_files(basedir: str):
    """
    Find all integration test files in $basedir/packages/@aws-cdk-testing/framework-integ .
    Include: test/**/*.ts
    Exclude: **.snapshot/, **/assets/

    Args:
        basedir (str): base directory of the repository
    """

    for file in glob.glob(
        f"{basedir}/packages/@aws-cdk-testing/framework-integ/**/test/**/integ.*.ts",
        recursive=True,
    ):
        if ".snapshot/" in file:
            continue
        if "/assets/" in file:
            continue
        yield file


def get_module_name(path: str):
    """
    Get module name from path
    Args:
        path (str): path to the file
    """
    path = re.sub(r".*/framework-integ/test/", "", path)
    return path.split("/")[0]


def get_test_name(path: str):
    """
    Get test name from path
    Args:
        path (str): path to the file
    """
    path = os.path.basename(path)
    path = path.replace("integ.", "")
    return os.path.splitext(path)[0]


def normalize_output_path(path: str) -> str:
    """
    Normalize output path to have 3 parts structure: constructs/package/module/file
    e.g. constructs/aws-cdk-lib/aws-s3/README.md

    Args:
        path (str): original path

    Returns:
        str: normalized path
    """
    # Remove common prefixes
    if "packages/@aws-cdk/" in path:
        # Alpha modules (@aws-cdk namespace)
        parts = path.split("packages/@aws-cdk/")[1].split("/")
        package = "@aws-cdk"
        module = parts[0]
    elif "packages/aws-cdk-lib/" in path:
        # Stable modules (aws-cdk-lib package)
        parts = path.split("packages/aws-cdk-lib/")[1].split("/")
        package = "aws-cdk-lib"
        module = parts[0]
    elif "framework-integ/test/" in path:
        module = get_module_name(path)
        package = "aws-cdk-lib"  # Default to aws-cdk-lib for integration tests
    else:
        # Default case for unknown paths
        package = "unknown"
        module = "unknown"

    # Get filename
    filename = os.path.basename(path)

    # Create 3-level directory structure
    return f"constructs/{package}/{module}/{filename}"
