import inspect
from dataclasses import dataclass
from typing import Any, Callable, get_origin


@dataclass
class Tool:
    name: str
    description: str
    fn: Callable[..., Any]
    schema: dict[str, Any]

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.fn(*args, **kwargs)


def _json_type(annotation: Any) -> str:
    if annotation in (int,):
        return "integer"
    if annotation in (float,):
        return "number"
    if annotation in (bool,):
        return "boolean"
    if annotation in (dict,) or get_origin(annotation) is dict:
        return "object"
    if annotation in (list,) or get_origin(annotation) is list:
        return "array"
    return "string"


def _build_schema(fn: Callable[..., Any]) -> dict[str, Any]:
    signature = inspect.signature(fn)
    properties: dict[str, dict[str, str]] = {}
    required: list[str] = []

    for name, param in signature.parameters.items():
        annotation = param.annotation if param.annotation is not inspect._empty else str
        properties[name] = {"type": _json_type(annotation)}
        if param.default is inspect._empty:
            required.append(name)

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


def tool(fn: Callable[..., Any]) -> Tool:
    """Decorator that wraps a function as a Simon tool."""

    return Tool(
        name=fn.__name__,
        description=(fn.__doc__ or "").strip() or f"Tool {fn.__name__}",
        fn=fn,
        schema=_build_schema(fn),
    )
