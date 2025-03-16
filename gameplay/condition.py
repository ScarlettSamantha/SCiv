from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Self


class ConditionalTypes(Enum):
    AND = 0
    OR = 1


class Condition:
    def __init__(self, *args, **kwargs):
        self._condition: Optional[Callable[..., bool]] = None
        self.params: Dict[str, Any] = kwargs
        self.required_params: List[str] = []
        self._validate_params()

    def _validate_params(self) -> None:
        """Check if all required parameters are provided."""
        missing_params = [param for param in self.required_params if param not in self.params]
        if missing_params:
            raise ValueError(f"Missing required parameters: {', '.join(missing_params)}")

    def set(self, condition: Callable[..., bool]) -> None:
        """Set the condition function."""
        self._condition = condition

    def _invoke_condition(self) -> bool:
        """Invoke the condition function safely."""
        if self._condition is None:
            return True

        try:
            return self._condition(**self.params)  # Unpacking self.params
        except TypeError as e:
            raise TypeError(f"Error invoking condition function: {e}") from e

    def is_met(self) -> bool:
        """Evaluate the condition function safely."""
        return self._invoke_condition()

    def __call__(self, *args: Any, **kwargs: Any) -> bool:
        """Invoke the condition check."""
        return self.is_met()

    @classmethod
    def no_condition(cls) -> Self:
        """Return a no-op condition."""
        return cls()


class Conditions:
    def __init__(self, *args, **kwargs):
        self._conditions: List[Condition] = []
        self.conditional_type: ConditionalTypes = ConditionalTypes.AND
        self.condition_params: Dict[str, Any] = {}

    def are_met(self, params: Dict[str, Any] = {}) -> bool:
        self.condition_params.update(params)
        """Evaluate all conditions based on the conditional type."""
        if self.conditional_type == ConditionalTypes.AND:
            for condition in self._conditions:
                if not condition(**self.condition_params):
                    return False
            return True
        elif self.conditional_type == ConditionalTypes.OR:
            for condition in self._conditions:
                if condition(**self.condition_params):
                    return True
            return False

        else:
            raise ValueError("Invalid conditional type")

    def add(self, condition: Condition) -> None:
        """Add a condition to the list."""
        self._conditions.append(condition)

    def remove(self, condition: Condition) -> None:
        """Remove a condition from the list."""
        self._conditions.remove(condition)

    def set_or(self) -> None:
        """Set the conditional type to OR."""
        self.conditional_type = ConditionalTypes.OR

    def set_and(self) -> None:
        """Set the conditional type to AND."""
        self.conditional_type = ConditionalTypes.AND

    def __call__(self, *args: Any, **kwargs: Any) -> bool:
        """Invoke the conditions check."""
        return self.are_met()

    @classmethod
    def no_conditions(cls) -> Self:
        """Return a no-op conditions group."""
        return cls()


class BuildCondition(Condition):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.required_params = ["tile", "improvement"]
