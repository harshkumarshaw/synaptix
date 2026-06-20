from app.routers.assets import router as assets
from app.routers.master_data import router as master_data
from app.routers.workflow import router as workflow

__all__ = [
    "master_data",
    "workflow",
    "assets",
]
