from typing import Any, Dict


class Government:
    pass

    def dump(self) -> Dict[str, Any]:
        data: Dict[str, Any] = self.__dict__.copy()
        return data
