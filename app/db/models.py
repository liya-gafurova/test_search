from sqlalchemy import String, Column, DateTime, func, sql

from app.db.base_class import Base


class Sources(Base):

    id = Column(String(50), primary_key=True)
    name = Column(String(200))
    filepath = Column(String(200))
    created = Column(DateTime(timezone=True), server_default=sql.func.now())