from simon.tools.tool import Tool, tool


class ToolRegistry:
    """Small registry for developer-provided tools."""

    def __init__(self, tools: list[Tool | object] | None = None) -> None:
        self._tools: dict[str, Tool] = {}
        for candidate in tools or []:
            self.register(candidate)

    def register(self, candidate: Tool | object) -> None:
        wrapped = candidate if isinstance(candidate, Tool) else tool(candidate)  # type: ignore[arg-type]
        self._tools[wrapped.name] = wrapped

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def schemas(self) -> list[dict[str, object]]:
        out: list[dict[str, object]] = []
        for t in self._tools.values():
            out.append(
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.schema,
                }
            )
        return out

    def names(self) -> list[str]:
        return list(self._tools.keys())
