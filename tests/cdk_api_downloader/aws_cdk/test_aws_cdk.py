from pytest_mock import MockerFixture
from cdk_api_downloader.aws_cdk.aws_cdk import (
    find_markdown_files,
    find_integ_test_files,
    get_module_name,
    get_test_name,
    surround_with_codeblock,
)
import io
import sys
from unittest.mock import mock_open, patch


def test_find_markdown_files(mocker: MockerFixture):
    expected_files = [
        "repositories/aws-cdk/packages/@aws-cdk/aws-s3/README.md",
        "repositories/aws-cdk/packages/aws-cdk-lib/aws-lakeformation/README.md",
        "repositories/aws-cdk/packages/aws-cdk-lib/aws-codeartifact/README.md",
        "repositories/aws-cdk/DEPRECATED_APIs.md",
    ]

    ignored_files = [
        "repositories/aws-cdk/packages/@aws-cdk-testing/framework-integ/test/aws-lambda-nodejs/test/integ.specifycode.js.snapshot/asset.1a1a5806c7ba6c308e1a83f863e2d6f1f82a6daeb20286116d4a8b049faf1506/README.md",
        "repositories/aws-cdk/packages/@aws-cdk-testing/cli-integ/resources/cli-regression-patches/v2.132.0/NOTES.md",
        "repositories/aws-cdk/packages/some-other-package/README.md",
    ]

    # glob.globのモックを設定
    mocker.patch(
        "glob.glob",
        side_effect=[
            # @aws-cdk パターン
            [expected_files[0]],
            # aws-cdk-lib パターン
            [expected_files[1], expected_files[2]],
            # DEPRECATED_APIs.md パターン
            [expected_files[3]],
        ],
    )
    
    # open関数のモックを設定
    mock_file_contents = {
        expected_files[0]: "# AWS S3\nThis is a readme",
        expected_files[1]: "# AWS Lakeformation\nThis is a readme",
        expected_files[2]: "# AWS CodeArtifact\nThis is a readme",
        expected_files[3]: "# Deprecated APIs\nList of deprecated APIs",
    }
    
    def mock_open_func(file, *args, **kwargs):
        content = mock_file_contents.get(file, "")
        return io.StringIO(content)
    
    # open関数をモック
    with patch("builtins.open", side_effect=mock_open_func):
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
            # DEPRECATED_APIs.md パターン
            [],
        ],
    )
    
    # open関数のモックを設定
    mock_file_contents = {
        files[0]: "# AWS Service\nThere are no hand-written examples.",
        files[1]: "# AWS Other\nThis is a valid readme",
    }
    
    def mock_open_func(file, *args, **kwargs):
        content = mock_file_contents.get(file, "")
        return io.StringIO(content)
    
    # open関数をモック
    with patch("builtins.open", side_effect=mock_open_func):
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


def test_surround_with_codeblock():
    codeblock = surround_with_codeblock(
        "mymodule", "test1", "console.log('hello world');"
    )
    assert (
        codeblock
        == """\
## mymodule / test1

```ts
console.log('hello world');
```

"""
    )
