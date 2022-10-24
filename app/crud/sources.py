from app.db.models import Sources
from app.crud.base import CRUDBase
from app.schemas import SourceDB


class CRUDSources(CRUDBase[Sources, SourceDB, SourceDB]):
    pass


crud_sources = CRUDSources(Sources)
