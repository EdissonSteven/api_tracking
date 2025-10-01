import logging
from typing import AsyncGenerator, Generator, Optional

from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker

try:
    from src.config.settings import get_settings
except ImportError:
    # Fallback settings
    def get_settings():
        class Settings:
            database_url = "postgresql://tracking_user:tracking_pass@postgres:5432/tracking_db"
            db_echo = False
        return Settings()

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gestor de conexiones a la base de datos (soporta sync y async engines)."""
    
    def __init__(self, database_url: Optional[str] = None, db_echo: Optional[bool] = None):
        settings = get_settings()
        self.database_url = (
            database_url
            or getattr(settings, "DATABASE_URL", None)
            or getattr(settings, "database_url", None)
        )
        self.db_echo = (
            db_echo
            if db_echo is not None
            else getattr(settings, "DB_ECHO", None)
            if getattr(settings, "DB_ECHO", None) is not None
            else getattr(settings, "db_echo", False)
        )

        # motores y factories (se inicializan en _setup_engine)
        self._sync_engine = None
        self._async_engine: Optional[AsyncEngine] = None
        self._session_factory = None

        self._setup_engine()
    
    def _setup_engine(self):
        """Configura engine sync o async según la URL y el driver."""
        connect_args = {}

        if self.database_url and "sqlite" in str(self.database_url):
            connect_args = {"check_same_thread": False}
            # sqlite suele usar StaticPool en tests/local
            self._sync_engine = create_engine(
                str(self.database_url),
                echo=self.db_echo if self.db_echo is not None else False,
                connect_args=connect_args,
                poolclass=StaticPool
            )
            self._async_engine = None
            self._session_factory = sessionmaker(self._sync_engine, class_=Session, expire_on_commit=False)
            return

        # Detectar driver async (p. ej. postgresql+asyncpg)
        if self.database_url and ("+asyncpg" in str(self.database_url) or "asyncpg" in str(self.database_url)):
            # crear engine async
            self._async_engine = create_async_engine(
                str(self.database_url),
                echo=self.db_echo if self.db_echo is not None else False,
                connect_args=connect_args,
                future=True,
            )
            self._sync_engine = None
            self._session_factory = sessionmaker(self._async_engine, class_=AsyncSession, expire_on_commit=False)
        else:
            # engine síncrono
            self._sync_engine = create_engine(
                str(self.database_url),
                echo=self.db_echo if self.db_echo is not None else False,
                connect_args=connect_args,
                future=True,
            )
            self._async_engine = None
            self._session_factory = sessionmaker(self._sync_engine, class_=Session, expire_on_commit=False)
    
    @property
    def engine(self):
        """Retorna el engine (async si existe, sino sync)."""
        return self._async_engine or self._sync_engine

    async def create_tables(self):
        """Crea las tablas; si el engine es async usa run_sync dentro de begin()."""
        try:
            if self._async_engine:
                async with self._async_engine.begin() as conn:
                    await conn.run_sync(SQLModel.metadata.create_all)
            else:
                SQLModel.metadata.create_all(self._sync_engine)
            logger.info("Tablas de base de datos creadas exitosamente")
        except Exception as e:
            logger.error(f"Error creando tablas: {e}", exc_info=True)
            raise

    def create_session(self) -> Session:
        """
        Crea una nueva sesión DIRECTA (no generador).
        IMPORTANTE: El caller debe cerrar la sesión manualmente.
        """
        if not self._sync_engine:
            raise RuntimeError("Sync engine no inicializado; use get_async_session para async engine")
        return self._session_factory()
    
    def get_session_generator(self) -> Generator[Session, None, None]:
        """Generador sync para sesiones (usa cuando hay engine síncrono)."""
        if not self._sync_engine:
            raise RuntimeError("Sync engine no inicializado; use get_async_session para async engine")
        session = self._session_factory()
        try:
            yield session
        finally:
            session.close()
    
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Generador async para sesiones cuando se usa engine async."""
        if not self._async_engine:
            # Si no hay async engine, exponer session sync de forma simple
            session = self._session_factory()
            try:
                yield session  # type: ignore
            finally:
                session.close()
            return

        async with self._session_factory() as session:
            yield session

    async def close(self):
        """Cierra conexiones; soporta async y sync engines."""
        try:
            if self._async_engine:
                await self._async_engine.dispose()
            elif self._sync_engine:
                self._sync_engine.dispose()
            logger.info("Conexiones de base de datos cerradas")
        except Exception as e:
            logger.error(f"Error cerrando conexiones: {e}", exc_info=True)
            raise

# Instancia global del gestor de base de datos
db_manager = DatabaseManager()

# CORRECCION PRINCIPAL: Dependency para FastAPI
def get_db_session():
    """
    Dependency para FastAPI que proporciona una sesión de base de datos.
    Este ES el generador principal - no llama a otro generador.
    """
    # Crear sesión directa (no generador)
    session = db_manager.create_session()
    try:
        yield session
        # FastAPI ejecutará esta parte después del endpoint
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def get_direct_session() -> Session:
    """
    Obtiene una sesión directa para uso manual.
    IMPORTANTE: El caller debe manejar commit/rollback/close manualmente.
    """
    return db_manager.create_session()

async def get_async_db_session() -> AsyncGenerator[Session, None]:
    """Función async para obtener sesión de BD (para FastAPI dependencies)."""
    async for session in db_manager.get_async_session():
        yield session

def init_database_sync():
    """Wrapper sync para creación de tablas si se desea correr en contexto sync."""
    if db_manager._sync_engine:
        SQLModel.metadata.create_all(db_manager._sync_engine)
    else:
        raise RuntimeError("No hay engine sync; use create_tables() async para engine async")

# Aliases para compatibilidad
engine = db_manager.engine