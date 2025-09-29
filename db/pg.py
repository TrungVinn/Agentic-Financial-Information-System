import os
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


_engine: Optional[Engine] = None


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL", "")
    if url:
        return url
    # Fallback to a local PostgreSQL default
    user = os.getenv("PGUSER", "postgres")
    password = os.getenv("PGPASSWORD", "postgres")
    host = os.getenv("PGHOST", "localhost")
    port = os.getenv("PGPORT", "5432")
    db = os.getenv("PGDATABASE", "djia")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(get_database_url())
    return _engine

