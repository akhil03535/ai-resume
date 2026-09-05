import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base

# Import every model module so Base.metadata is fully populated before any
# table (including cross-module FKs) is created for the test DB.
from app.users import models as _users_models  # noqa: F401
from app.profiles import models as _profiles_models  # noqa: F401
from app.skills import models as _skills_models  # noqa: F401
from app.jobs import models as _jobs_models  # noqa: F401
from app.resumes import models as _resumes_models  # noqa: F401
from app.analysis import models as _analysis_models  # noqa: F401


@pytest.fixture()
def db_session():
    """In-memory SQLite session for fast unit tests that don't need real
    Postgres-only features (JSON columns behave fine here for our use)."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
