import io
from unittest.mock import patch

from pytest_mock import MockerFixture

from cdk_api_downloader.aws_cdk.aws_cdk import (
    find_integ_test_files,
    find_markdown_files,
    get_module_name,
    get_test_name,
    normalize_output_path,
)


def test_find_markdown_files(mocker: MockerFixture):
    expected_files = [
        "repositories/aws-cdk/packages/@aws-cdk/aws-s3/README.md",
        "repositories/aws-cdk/packages/aws-cdk-lib/aws-lakeformation/README.md",
        "repositories/aws-cdk/packages/aws-cdk-lib/aws-codeartifact/README.md",
    ]

    # glob.globのモックを設定
    mocker.patch(
        "glob.glob",
        side_effect=[
            # @aws-cdk パターン
            [expected_files[0]],
            # aws-cdk-lib パターン
            [expected_files[1], expected_files[2]],
        ],
    )

    # open関数のモックを設定
    mock_file_contents = {
        expected_files[0]: "# AWS S3\nThis is a readme",
        expected_files[1]: "# AWS Lakeformation\nThis is a readme",
        expected_files[2]: "# AWS CodeArtifact\nThis is a readme",
    }

    def mock_open_func(file, encoding=None):
        content = mock_file_contents.get(file, "")
        return io.StringIO(content)

    # open関数をモック
    with patch("builtins.open", mock_open_func):
        result = list(find_markdown_files("repositories/aws-cdk"))
        assert sorted(result) == sorted(expected_files)


def test_find_markdown_files_excludes_handwritten(mocker: MockerFixture):
    files = [
        "repositories/aws-cdk/packages/aws-cdk-lib/aws-service/README.md",
        "repositories/aws-cdk/packages/@aws-cdk/aws-other/README.md",
    ]

    # glob.globのモックを設定
    mocker.patch(
        "glob.glob",
        side_effect=[
            # @aws-cdk パターン
            [files[1]],
            # aws-cdk-lib パターン
            [files[0]],
        ],
    )

    # open関数のモックを設定
    mock_file_contents = {
        files[0]: "# AWS Service\nThere are no hand-written examples.",
        files[1]: "# AWS Other\nThis is a valid readme",
    }

    def mock_open_func(file, encoding=None):
        content = mock_file_contents.get(file, "")
        return io.StringIO(content)

    # open関数をモック
    with patch("builtins.open", mock_open_func):
        result = list(find_markdown_files("repositories/aws-cdk"))
        # "There are no hand-written"を含むファイルは除外されるはず
        assert result == [files[1]]


def test_find_integ_test_files(mocker: MockerFixture):
    expected_files = [
        "repositories/aws-cdk/packages/@aws-cdk-testing/framework-integ/test/aws-config/test/integ.rule.ts",
        "repositories/aws-cdk/packages/@aws-cdk-testing/framework-integ/test/aws-config/test/integ.rule2.ts",
    ]

    ignored_files = [
        "repositories/aws-cdk/packages/@aws-cdk-testing/framework-integ/test/aws-config/test/hoge.snapshot/integ.rule3.ts",
        "repositories/aws-cdk/packages/@aws-cdk-testing/framework-integ/test/aws-config/test/assets/integ.rule3.ts",
    ]

    mocker.patch(
        "glob.glob",
        return_value=expected_files + ignored_files,
    )
    integ_test_files = find_integ_test_files("repositories/aws-cdk")
    assert list(integ_test_files) == expected_files


def test_get_module_name():
    module_name = get_module_name(
        "repositories/aws-cdk/packages/@aws-cdk-testing/framework-integ/test/aws-config/test/integ.rule.ts"
    )
    assert module_name == "aws-config"


def test_get_test_name():
    test_name = get_test_name(
        "repositories/aws-cdk/packages/@aws-cdk-testing/framework-integ/test/aws-config/test/integ.rule.ts"
    )
    assert test_name == "rule"


def test_normalize_output_path():
    # @aws-cdk パッケージのテスト
    path = "repositories/aws-cdk/packages/@aws-cdk/aws-s3/README.md"
    normalized = normalize_output_path(path)
    assert normalized == "constructs/@aws-cdk/aws-s3/README.md"

    # aws-cdk-lib パッケージのテスト
    path = "repositories/aws-cdk/packages/aws-cdk-lib/aws-lambda/README.md"
    normalized = normalize_output_path(path)
    assert normalized == "constructs/aws-cdk-lib/aws-lambda/README.md"

    # integ-test ファイルのテスト
    path = "repositories/aws-cdk/packages/@aws-cdk-testing/framework-integ/test/aws-config/test/integ.rule.ts"
    normalized = normalize_output_path(path)
    assert normalized == "constructs/aws-cdk-lib/aws-config/integ.rule.ts"

    # 不明なパスのテスト
    path = "repositories/aws-cdk/some/unknown/path/file.md"
    normalized = normalize_output_path(path)
    assert normalized == "constructs/unknown/unknown/file.md"
