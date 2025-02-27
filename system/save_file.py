from abc import ABC, abstractmethod
from typing import Any, Dict, List
import zlib
import gzip
import json
import sys
from pathlib import Path
from system.vars import APPLICATION_NAME


class BaseSaver(ABC):
    base_path: str = "./saves"
    extension: str = ""
    game_name: str = APPLICATION_NAME
    compression_enabled: bool = False

    def __init__(
        self,
    ):
        self.data: str
        self.meta_data: Dict[str, Any]  # Will be converted to json
        self.identifier: str
        self.hash: str

    def set_identifier(self, identifier: str):
        self.identifier = identifier

    def set_data(self, data: str):
        self.data = data
        self.hash = str(zlib.crc32(data.encode("utf-8")))

    def set_meta_data(self, meta_data: Dict[str, Any]):
        self.meta_data = meta_data

    def set_hash(self, hash: str):
        self.hash = hash

    def get_identifier(self) -> str:
        return self.identifier

    def get_data(self, data: str) -> str:
        return self.data

    def get_meta_data(self) -> Dict[str, Any]:
        return self.meta_data

    def get_hash(self) -> str:
        return self.hash

    @abstractmethod
    def save(self) -> bool: ...

    @abstractmethod
    def load(self) -> Any: ...

    @abstractmethod
    def get_saved_session(self) -> List[str]: ...

    @abstractmethod
    def get_saved_meta_data(self) -> Dict[str, Any]: ...

    def compress_data(self, data: bytes) -> bytes:
        """Compress data using gzip if enabled."""
        if self.compression_enabled:
            return gzip.compress(data)
        return data

    def decompress_data(self, data: bytes) -> bytes:
        """Decompress data if compression is enabled."""
        if self.compression_enabled:
            return gzip.decompress(data)
        return data

    def identify_save_location(self) -> str:
        if self.base_path is None:
            if sys.platform == "win32":
                return str(Path.home() / "AppData" / "Local" / self.game_name)
            elif sys.platform == "darwin":
                return str(Path.home() / "Library" / "Application Support" / self.game_name)
            elif sys.platform.startswith("linux") or sys.platform.startswith("unix"):
                return str(Path.home() / ".local" / "share" / self.game_name)  # Standard Linux user data location
        else:
            return str(Path(self.base_path) / self.game_name)
        raise RuntimeError("Unsupported operating system: " + sys.platform)

    def generate_save_directory(self) -> str:
        return str(Path(self.identify_save_location()) / self.identifier)

    def generate_save_path(self, filename: str) -> str:
        return str(Path(self.generate_save_directory()) / filename)

    def compare_hash(self, data: str) -> bool:
        return self.hash == str(zlib.crc32(data.encode("utf-8")))


class SavePickleFile(BaseSaver):
    base_path = "saves"
    compression_enabled = True
    extension = "pickle.gz" if compression_enabled else "pickle"

    def save(self) -> bool:
        if self.base_path is None:
            raise RuntimeError("Base path is not set.")

        save_dir = Path(self.base_path) / self.identifier
        save_dir.mkdir(parents=True, exist_ok=True)

        data_path = save_dir / f"data.{self.extension}"
        metadata_path = save_dir / "metadata.json"
        hash_path = save_dir / "hash.txt"

        compressed_data: bytes = self.compress_data(self.data.encode("utf-8"))

        try:
            with open(data_path, "wb") as file:
                file.write(compressed_data)

            with open(metadata_path, "w", encoding="utf-8") as file:
                json.dump(self.meta_data, file, indent=4)

            with open(hash_path, "w", encoding="utf-8") as file:
                file.write(self.hash)

            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False

    def load(self) -> str | bool:
        save_dir = Path(self.base_path) / self.identifier
        data_path = save_dir / f"data.{self.extension}"
        metadata_path = save_dir / "metadata.json"
        hash_path = save_dir / "hash.txt"

        try:
            with open(data_path, "rb") as file:
                data = file.read()
                self.data = self.decompress_data(data).decode("utf-8")

            with open(metadata_path, "r", encoding="utf-8") as file:
                self.meta_data = json.load(file)

            with open(hash_path, "r", encoding="utf-8") as file:
                self.hash = file.read().strip()

            if not self.compare_hash(self.data):
                print("Warning: Data integrity check failed!")
                return False

            return self.data
        except FileNotFoundError:
            return False

    def get_saved_session(self) -> List[str]:
        directory = Path(self.base_path)

        if not directory.exists():
            return []

        return [d.name for d in directory.iterdir() if d.is_dir()]

    def get_saved_meta_data(self) -> Dict[str, Dict[Any, Any]]:
        directory = Path(self.base_path)
        meta_data_list: Dict[str, Dict[Any, Any]] = {}

        if not directory.exists():
            return meta_data_list

        for save_folder in directory.iterdir():
            if save_folder.is_dir():
                metadata_path = save_folder / "metadata.json"
                if metadata_path.exists():
                    with open(metadata_path, "r", encoding="utf-8") as file:
                        meta_data_list[save_folder.name] = json.load(file)

        return meta_data_list
