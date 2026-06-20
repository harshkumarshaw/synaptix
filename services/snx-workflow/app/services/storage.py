import os
import uuid
from abc import ABC, abstractmethod
from app.config import get_settings


class StorageProvider(ABC):
    @abstractmethod
    async def save(self, file_name: str, content: bytes, tenant_id: uuid.UUID) -> str:
        """Save a file and return its storage path string."""
        pass

    @abstractmethod
    async def read(self, storage_path: str) -> bytes:
        """Read a file's content bytes from its storage path."""
        pass

    @abstractmethod
    async def delete(self, storage_path: str) -> None:
        """Delete a file from storage."""
        pass


class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: str | None = None):
        settings = get_settings()
        self.base_dir = base_dir or settings.storage_dir

    async def save(self, file_name: str, content: bytes, tenant_id: uuid.UUID) -> str:
        # Create tenant-specific directory
        tenant_dir = os.path.join(self.base_dir, str(tenant_id))
        os.makedirs(tenant_dir, exist_ok=True)
        
        # Generate a unique path to avoid collisions
        unique_name = f"{uuid.uuid4()}_{file_name}"
        full_path = os.path.join(tenant_dir, unique_name)
        
        with open(full_path, "wb") as f:
            f.write(content)
            
        return full_path

    async def read(self, storage_path: str) -> bytes:
        if not os.path.exists(storage_path):
            raise FileNotFoundError(f"File not found at: {storage_path}")
        with open(storage_path, "rb") as f:
            return f.read()

    async def delete(self, storage_path: str) -> None:
        if os.path.exists(storage_path):
            os.remove(storage_path)
