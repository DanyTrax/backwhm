import os


def pytest_configure(config):
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_app.db")
    os.environ.setdefault("SESSION_SECRET", "unit-test-session-secret-32chars-minimum!!")
    os.environ.setdefault("CSRF_SECRET", "unit-test-csrf-secret-32chars-minimum!!!!")
    os.environ.setdefault("INITIAL_ADMIN_PASSWORD", "test-admin-pass-123")
