"""Pytest configuration file."""

import pytest

# Register asyncio marker
def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: mark test as an asyncio coroutine")
