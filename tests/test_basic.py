"""基本的なテスト"""


def test_import_cdk_api_mcp_server():
    """cdk_api_mcp_serverがインポートできることを確認"""
    import cdk_api_mcp_server

    assert cdk_api_mcp_server is not None


def test_import_cdk_api_downloader():
    """cdk_api_downloaderがインポートできることを確認"""
    import cdk_api_downloader

    assert cdk_api_downloader is not None
