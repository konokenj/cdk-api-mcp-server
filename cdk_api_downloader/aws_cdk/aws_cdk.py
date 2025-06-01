import glob
import os
import re


def find_markdown_files(basedir: str):
    """
    Find markdown files in $basedir.
    Include: 
        - packages/@aws-cdk/**/*.md
        - packages/aws-cdk-lib/**/*.md
        - DEPRECATED_APIs.md
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
        f"{basedir}/DEPRECATED_APIs.md",
    ]
    
    for pattern in patterns:
        for file in glob.glob(pattern, recursive=True):
            # 除外条件をチェック
            if "cli-regression-patches/" in file or ".snapshot/" in file:
                continue
                
            # ファイルの内容をチェック
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if "There are no hand-written" in content:
                        continue
            except Exception:
                # ファイル読み込みエラーの場合はスキップ
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
    path = path.split("/")[0]
    return path


def get_test_name(path: str):
    """
    Get test name from path
    Args:
        path (str): path to the file
    """
    path = os.path.basename(path)
    path = path.replace("integ.", "")
    path = os.path.splitext(path)[0]
    return path


def surround_with_codeblock(module_name: str, test_name: str, content: str):
    """
    Surround with codeblock
    Args:
        content (str): content to surround with codeblock
    """
    return f"## {module_name} / {test_name}\n\n```ts\n{content}\n```\n\n"
