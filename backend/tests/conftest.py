"""
Pytest configuration and global fixtures.
Initializes Beanie and MongoDB for test runs.
"""

import asyncio
import pytest
from app.db.init_db import init_db


@pytest.fixture(scope="session", autouse=True)
def initialize_database():
    """Ensure database and Beanie documents are initialized for all tests."""
    asyncio.run(init_db())
