import gzip
import json
import sys
import zlib
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from system.vars import APPLICATION_NAME


class BaseSaver(ABC):
    base_path: str = "./saves"
    extension: str = ""
    game_name: str = APPLICATION_NAME
    compression_enabled: bool = False

    def __init__(
        self,
    ):
        self.data: bytes
        self.meta_data: Dict[str, Any]  # Will be converted to json
        self.identifier: str
        self.hash: str
        self.counter: int = 0
        self.inject_metadata: bool = True
        self.loaded_data_length: int = 0

    def set_identifier(self, identifier: str):
        self.identifier = identifier

    def set_data(self, data: bytes):
        self.data = data
        self.hash = str(zlib.crc32(data))

    def set_meta_data(self, meta_data: Dict[str, Any]):
        self.meta_data = meta_data

    def set_hash(self, hash: str):
        self.hash = hash

    def set_session_incrementor(self, counter_increment_value: int) -> None:
        self.counter = counter_increment_value

    def get_identifier(self) -> str:
        return self.identifier

    def get_data(self) -> bytes:
        return self.data

    def get_meta_data(self) -> Dict[str, Any]:
        return self.meta_data

    def get_hash(self) -> str:
        return self.hash

    def get_session_incrementor(self) -> int:
        return self.counter

    def cycle_incrementor(self, amount: int = 1) -> int:
        self.counter += amount
        return self.counter

    def register_modifications_metadata(self) -> Dict[str, str] | None:
        if not self.inject_metadata:
            return None

        self.meta_data["saver"] = {
            "class": self.__class__.__name__,
            "compression": self.compression_enabled,
            "checksum_crc32": self.hash,
            "meta_checksum_crc32": "",
            "extension": self.extension,
            "game_name": self.game_name,
            "base_path": self.base_path,
        }

        self.meta_data["saver"]["meta_checksum_crc32"] = str(zlib.crc32(repr(self.meta_data).encode()))
        self.meta_data["saver"]["data_size"] = len(self.data)
        self.meta_data["saver"]["save_time"] = datetime.now().isoformat()

    @abstractmethod
    def save(self) -> bool: ...

    @abstractmethod
    def load(self) -> Any: ...

    def get_saved_session(self) -> List[str]:
        save_location = Path(self.identify_save_location())
        if not save_location.exists():
            return []

        result = []
        for d in save_location.iterdir():
            if d.is_dir() and d.name != "metadata.json":
                result.append(d.name)

        return result

    def get_session_data(self) -> None | Dict[str, Any]:
        save_location = Path(self.identify_save_location())

        if not save_location.exists():
            return None

        save_location = save_location / self.identifier

        if not save_location.exists():
            return None

        if (save_location / "metadata.json").exists():
            meta_data = json.loads((save_location / "metadata.json").read_text())
            return meta_data

        return None

    @abstractmethod
    def get_saved_meta_data(self) -> Dict[str, Any]: ...

    def compress_and_inject_data(self, data: bytes) -> bytes:
        """Compress data using gzip if enabled."""

        if self.inject_metadata:
            self.register_modifications_metadata()
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
            return str((Path(self.base_path)).absolute())
        raise RuntimeError("Unsupported operating system: " + sys.platform)

    def generate_save_directory(self) -> str:
        return str(Path(self.identify_save_location()) / self.identifier)

    def generate_save_path(self, filename: str) -> str:
        return str(Path(self.generate_save_directory()) / filename)

    def compare_hash(self, data: bytes) -> bool:
        return self.hash == str(zlib.crc32(data))


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

        compressed_data: bytes = self.compress_and_inject_data(self.data)

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

    def load(self) -> bytes | bool:
        save_dir = Path(self.base_path) / self.identifier
        data_path = save_dir / f"data.{self.extension}"
        metadata_path = save_dir / "metadata.json"
        hash_path = save_dir / "hash.txt"

        try:
            with open(data_path, "rb") as file:
                data = file.read()
                self.data = self.decompress_data(data)

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

        metadata_path = directory / self.identifier / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, "r", encoding="utf-8") as file:
                meta_data_list = json.load(file)

        return meta_data_list
