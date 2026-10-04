"""Conexión a la base de datos: motor,
fábrica de sesiones y creación de tablas"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from bbva_rag.memory.models import Base


def create_session_factory(database_url: str, **engine_options) -> sessionmaker[Session]:
    engine = create_engine(database_url, pool_pre_ping=True, **engine_options)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)
