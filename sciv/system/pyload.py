import ast
import fnmatch
import importlib
import importlib.util
import inspect
import os
import re
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

from helpers.debug import Debug
from managers.log import LogManager


def load_class(module_name: str, class_name: str) -> Type[Any]:
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


class GenericClassVisitor(ast.NodeVisitor):
    def __init__(self, properties: List[Tuple[str, str]] = []) -> None:
        self.subclasses: List[str] = []
        self.properties = properties

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.subclasses.append(node.name)
        self.generic_visit(node)


class PyFileProcessor:
    def __init__(
        self,
        base_classes: Union[Type[Any], List[Type[Any]], Optional[Callable[[str, str], bool]]] = None,
        properties: Optional[Tuple[str, str]] = None,
        _skip_on_error: bool = False,
        log_errors: bool = True,
        package: Optional[str] = None,
    ):
        self.base_classes: Optional[Union[Type[Any], List[Type[Any]], Callable[[str, str], bool]]] = base_classes
        self.properties: Optional[Tuple[str, str]] = properties
        self._skip_on_error: bool = _skip_on_error
        self.log_debug = log_errors
        self.package: Optional[str] = package
        self.base_dir: Optional[str] = None

    def process_file(self, file: str, name_pattern: Union[str, Callable[[str], bool]]) -> Dict[str, Type[Any]]:
        if not self._matches_pattern(file, name_pattern):
            return {}

        if Debug.system_loading_classes():
            LogManager.get_singleton_instance().engine.debug(f"Processing file: {file}")
        file_content = self._read_file(file)
        if not file_content:
            return {}

        return self._extract_classes(file, file_content)

    def _is_regex_pattern(self, pattern: str) -> bool:
        return pattern.endswith("$")

    def _matches_pattern(self, file: str, name_pattern: Union[str, Callable[[str], bool]]) -> bool:
        file_name = os.path.basename(file)
        if isinstance(name_pattern, Callable):
            return re.match(r"^(?!_).*.py$", file_name) is not None and name_pattern(file)

        if self._is_regex_pattern(name_pattern):
            regex_pattern = name_pattern
            try:
                return (
                    re.match(r"^(?!_).*.py$", file_name) is not None and re.match(regex_pattern, file_name) is not None
                )
            except re.error as e:
                if self.log_debug:
                    LogManager.get_singleton_instance().engine.error(
                        f"Invalid regex pattern: {regex_pattern}, error: {e}"
                    )
                return False
        else:
            return re.match(r"^(?!_).*.py$", file_name) is not None and fnmatch.fnmatch(file_name, name_pattern)

    def _read_file(self, file: str) -> Optional[str]:
        try:
            with open(file, "r") as f:
                return f.read()
        except IOError as e:
            if self._skip_on_error:
                LogManager.get_singleton_instance().engine.debug(f"Skipping {file} due to IO error: {e}")
            else:
                raise e
            return None

    def _filter_classes(self, classes: Dict[str, Type[Any]]) -> Dict[str, Type[Any]]:
        if callable(self.base_classes):
            return classes

        filtered_classes: Dict[str, Type[Any]] = {}

        def _filter_class(_class: Type[Any], allowed: Union[List[Type[Any]], Type[Any], str, None]) -> bool:
            if allowed is None:
                return True

            if isinstance(allowed, list):
                for allowed_class in allowed:
                    if issubclass(_class, allowed_class):
                        return True

            elif isinstance(allowed, str):
                if _class.__name__ == allowed or any(base.__name__ == allowed for base in _class.__bases__):
                    return True

            elif inspect.isclass(allowed):
                if issubclass(_class, allowed):
                    return True

                for base in _class.__bases__:
                    if base == allowed or base.__name__ == allowed.__name__:
                        return True

            if Debug.system_loading_classes():
                LogManager.get_singleton_instance().engine.debug(
                    f"Skipping class: {_class.__name__} due to base class mismatch {allowed}"
                )

            return False

        for class_name, _class in classes.items():
            if _filter_class(_class, self.base_classes):
                filtered_classes[class_name] = _class

        return filtered_classes

    def _extract_classes(self, file: str, file_content: str) -> Dict[str, Type[Any]]:
        loaded_classes: Dict[str, Type[Any]] = {}
        try:
            tree = ast.parse(file_content)
            visitor = GenericClassVisitor(properties=[self.properties] if self.properties is not None else [])
            visitor.visit(tree)
            loaded_classes = self._filter_classes(self._load_classes_from_visitor(visitor, file, package=self.package))
        except SyntaxError as e:
            if not self._skip_on_error:
                raise e
            LogManager.get_singleton_instance().engine.debug(f"Skipping {file} due to syntax error: {e}")
        return loaded_classes

    def _load_classes_from_visitor(
        self, visitor: GenericClassVisitor, file: str, package: Optional[str] = None
    ) -> Dict[str, Type[Any]]:
        loaded: Dict[str, Type[Any]] = {}

        if package:
            rel_path = os.path.splitext(os.path.relpath(file, self.base_dir))[0]
            mod_path = f"{package}.{rel_path.replace(os.sep, '.')}"
            module = importlib.import_module(mod_path)
        else:
            spec = importlib.util.spec_from_file_location(os.path.splitext(os.path.basename(file))[0], file)
            if not spec or not spec.loader:
                LogManager.get_singleton_instance().engine.error(f"Loader not found for file {file}")
                return {}
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore

        for cls_name in visitor.subclasses:
            if inspect.isfunction(self.base_classes):
                if self.base_classes(module, cls_name):  # type: ignore
                    loaded[cls_name] = getattr(module, cls_name)
            else:
                loaded[cls_name] = getattr(module, cls_name)
        return loaded


class PyLoad:
    def __init__(
        self,
        directory: Union[str, List[str]],
        name_pattern: Union[str, Callable[[str], bool]] = r"^(?!_).*.py$",
        base_classes: Union[Any, List[Any], Callable[[str, str], bool]] = None,
        properties: Tuple[str, str] | None = None,
        package: Optional[str] = None,
    ):
        self.directory: Union[str, List[str]] = directory
        if isinstance(directory, str):
            base_path = os.path.abspath(directory)
        else:
            base_path = os.path.abspath(directory[0])

        split_path = base_path.split(os.sep)

        self.package = package if package is not None else ".".join(split_path[-2:])

        self.name_pattern: Union[str, Callable[[str], bool]] = name_pattern
        self.base_classes: Union[Type[Any], List[Type[Any]], Callable[[str, str], bool]] = base_classes
        self.properties: Optional[Tuple[str, str]] = properties
        self.processor: PyFileProcessor = PyFileProcessor(base_classes, properties, package=self.package)
        self.processor.base_dir = directory if isinstance(directory, str) else directory[0]

    @classmethod
    def load_classes(
        cls,
        directory: Union[str, List[str]],
        name_pattern: Union[str, Callable[[str], bool]] = r"^(?!_).*.py$",
        base_classes: Union[Any, List[Any], Callable[[str, str], bool]] = None,
        properties: Optional[Tuple[str, str]] = None,
        *,
        package: Optional[str] = None,
    ) -> Dict[str, Type[Any]]:
        return cls(directory, name_pattern, base_classes, properties, package=package).load()

    def load(self) -> Dict[str, Type[Any]]:
        if isinstance(self.directory, list):
            out: Dict[str, Type[Any]] = {}
            for d in self.directory:
                out.update(self._process_folder(d))
            return out
        return self._process_folder(self.directory)

    def _process_folder(self, folder: str) -> Dict[str, Type[Any]]:
        loaded: Dict[str, Type[Any]] = {}
        for entry in os.listdir(folder):
            path = os.path.join(folder, entry)
            if os.path.isdir(path):
                if entry.startswith(".") or entry.startswith("__"):
                    continue
                loaded.update(self._process_folder(path))
            elif os.path.isfile(path):
                loaded.update(self.processor.process_file(path, self.name_pattern))
        return loaded
