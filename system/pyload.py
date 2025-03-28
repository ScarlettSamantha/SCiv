import ast
import fnmatch
import importlib
import importlib.util
import inspect
import os
import re
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

from managers.log import LogManager


def load_class(module_name: str, class_name: str):
    """Dynamically loads a class from a given module."""
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


class GenericClassVisitor(ast.NodeVisitor):
    def __init__(self, properties: List[Tuple[str, str]] = []):
        self.subclasses: List[str] = []
        self.properties: List[Tuple[str, str]] = properties

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.subclasses.append(node.name)
        self.generic_visit(node)


class PyFileProcessor:
    def __init__(
        self,
        base_classes: Union[Type, List[Type], Optional[Callable[[str, str], bool]]] = None,
        properties: Optional[Tuple[str, str]] = None,
        _skip_on_error: bool = False,
    ):
        self.base_classes: Optional[Union[Type, List[Type], Callable[[str, str], bool]]] = base_classes
        self.properties: Optional[Tuple[str, str]] = properties
        self._skip_on_error: bool = _skip_on_error

    def process_file(self, file: str, name_pattern: Union[str, Callable[[str], bool]]) -> Dict[str, Type]:
        if not self._matches_pattern(file, name_pattern):
            self._log_skip(file, name_pattern)
            return {}

        LogManager.get_instance().engine.debug(f"Processing file: {file}")
        file_content = self._read_file(file)
        if not file_content:
            return {}

        return self._extract_classes(file, file_content)

    def _is_regex_pattern(self, pattern: str) -> bool:
        """
        Detects if the provided string pattern is a regex pattern.
        """
        return pattern.endswith("$")

    def _matches_pattern(self, file: str, name_pattern: Union[str, Callable[[str], bool]]) -> bool:
        """
        Checks if the file matches the specified name pattern.
        Supports both string patterns and callable functions.
        """
        file_name = os.path.basename(file)
        if isinstance(name_pattern, Callable):
            return re.match(r"^(?!_).*.py$", file_name) is not None and name_pattern(file)
        elif isinstance(name_pattern, str):
            if self._is_regex_pattern(name_pattern):
                # Strip the leading 'r' and the quotes from the regex pattern
                regex_pattern = name_pattern
                try:
                    return (
                        re.match(r"^(?!_).*.py$", file_name) is not None
                        and re.match(regex_pattern, file_name) is not None
                    )
                except re.error as e:
                    LogManager.get_instance().engine.error(f"Invalid regex pattern: {regex_pattern}, error: {e}")
                    return False
            else:
                return re.match(r"^(?!_).*.py$", file_name) is not None and fnmatch.fnmatch(file_name, name_pattern)
        return False

    def _log_skip(self, file: str, name_pattern: Union[str, Callable[[str], bool]]) -> None:
        """
        Logs a message indicating that the file is skipped due to a pattern mismatch.
        """
        pattern = name_pattern if isinstance(name_pattern, str) else f"Custom->{name_pattern.__name__}"
        LogManager.get_instance().engine.debug(f"Skipping {file} due to name pattern[{pattern}] mismatch")

    def _read_file(self, file: str) -> Optional[str]:
        """
        Reads the content of the file and returns it as a string.
        Returns None if an IOError occurs.
        """
        try:
            with open(file, "r") as f:
                return f.read()
        except IOError as e:
            if self._skip_on_error:
                LogManager.get_instance().engine.debug(f"Skipping {file} due to IO error: {e}")
            else:
                raise e
            return None

    def _filter_classes(self, classes: Dict[str, Type]) -> Dict[str, Type]:
        """
        Filters the classes based on the provided criteria.
        """
        # If base_classes is a callable, skip filtering at this stage.
        if callable(self.base_classes):
            return classes

        filtered_classes: Dict[str, Type] = {}

        def _filter_class(_class: Type, allowed: Union[List[Type], Type, str, None]) -> bool:
            # Check if no base classes are provided
            if allowed is None:
                return True

            # Check if allowed is a list of types
            if isinstance(allowed, list):
                for allowed_class in allowed:
                    if issubclass(_class, allowed_class):
                        return True
            # Check if allowed is a string representing a class name
            elif isinstance(allowed, str):
                if _class.__name__ == allowed or any(base.__name__ == allowed for base in _class.__bases__):
                    return True
            # Check if allowed is an inspect class
            elif inspect.isclass(allowed):
                if issubclass(_class, allowed):
                    return True
                for base in _class.__bases__:
                    if base == allowed or base.__name__ == allowed.__name__:
                        return True

            LogManager.get_instance().engine.debug(
                f"Skipping class: {_class.__name__} due to base class mismatch {allowed}"
            )
            return False

        for class_name, _class in classes.items():
            if _filter_class(_class, self.base_classes):
                filtered_classes[class_name] = _class

        return filtered_classes

    def _extract_classes(self, file: str, file_content: str) -> Dict[str, Type]:
        """
        Parses the file content to extract class definitions.
        Uses GenericClassVisitor to find classes and loads them.
        """
        loaded_classes: Dict[str, Type] = {}
        try:
            tree = ast.parse(file_content)
            visitor = GenericClassVisitor(properties=[self.properties] if self.properties is not None else [])
            visitor.visit(tree)
            loaded_classes = self._filter_classes(self._load_classes_from_visitor(visitor, file))
        except SyntaxError as e:
            if not self._skip_on_error:
                raise e
            LogManager.get_instance().engine.debug(f"Skipping {file} due to syntax error: {e}")
        return loaded_classes

    def _load_classes_from_visitor(self, visitor: GenericClassVisitor, file: str) -> Dict[str, Type]:
        """
        Loads classes from the visitor's results using importlib.
        """
        loaded_classes: Dict[str, Type] = {}
        module_name = os.path.splitext(os.path.basename(file))[0]
        spec = importlib.util.spec_from_file_location(module_name, file)
        if spec is None or spec.loader is None:
            LogManager.get_instance().engine.error(f"Loader not found for module: {module_name}")
            return {}
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for class_name in visitor.subclasses:
            LogManager.get_instance().engine.debug(f"Found class: {class_name}")
            if inspect.isfunction(self.base_classes):
                if self.base_classes(module, class_name):
                    loaded_classes[class_name] = getattr(module, class_name)
            else:
                loaded_classes[class_name] = getattr(module, class_name)
        return loaded_classes


class PyLoad:
    """
    Loads and returns classes from Python files in the given directory based on the provided criteria.

    :param directory: Directory to search for Python files.
    :param name_pattern: File name pattern to match Python files.
    :param base_classes: Base class or list of base classes to match subclasses.
    :param properties: List of tuples containing class property names and values to match.
    :return: Dictionary of class names and their corresponding types.
    """

    def __init__(
        self,
        directory: Union[str, List[str]],
        name_pattern: Union[str, Callable[[str], bool]] = r"^(?!_).*.py$",
        base_classes: Union[Any, List[Any], Callable[[str, str], bool]] = None,
        properties: Tuple[str, str] | None = None,
        *args,
        **kwargs,
    ):
        self.directory: Union[str, List[str]] = directory
        self.name_pattern: Union[str, Callable[[str], bool]] = name_pattern
        self.base_classes: Union[Type, List[Type], Callable[[str, str], bool]] = base_classes
        self.properties: Optional[Tuple[str, str]] = properties
        self.processor: PyFileProcessor = PyFileProcessor(base_classes, properties)

    @classmethod
    def load_classes(
        cls,
        directory: Union[str, List[str]],
        name_pattern: Union[str, Callable[[str], bool]] = r"^(?!_).*.py$",
        base_classes: Union[Any, List[Any], Callable[[str, str], bool]] = None,
        properties: Optional[Tuple[str, str]] = None,
    ) -> Dict[str, Type]:
        """
        Loads and returns classes from Python files in the given directory based on the provided criteria.

        :param directory: Directory to search for Python files.
        :param name_pattern: File name pattern to match Python files.
        :param base_classes: Base class or list of base classes to match subclasses.
        :param properties: List of tuples containing class property names and values to match.
        :return: Dictionary of class names and their corresponding types.
        """
        return cls(directory, name_pattern, base_classes, properties).load()

    def load(self) -> Dict[str, Type]:
        """
        Loads classes from the specified directory or directories.
        """
        if isinstance(self.directory, list):
            loaded_classes: Dict[str, Type] = {}
            for _dir in self.directory:
                loaded_classes.update(self._process_folder(_dir))
            return loaded_classes
        return self._process_folder(self.directory)

    def _process_folder(self, folder: str) -> Dict[str, Type]:
        """
        Recursively processes folders and loads classes from Python files.
        """
        loaded_classes: Dict[str, Type] = {}
        for file in os.listdir(folder):
            file_path = os.path.join(folder, file)
            if os.path.isdir(file_path):
                loaded_classes.update(self._process_folder(file_path))
            elif os.path.isfile(file_path):
                loaded_classes.update(self.processor.process_file(file_path, self.name_pattern))
        return loaded_classes
