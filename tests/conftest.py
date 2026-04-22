"""Variables de entorno antes de importar la app (bootstrap síncrono + SQLite en pruebas)."""

import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./.pytest_backup_whm.db")
