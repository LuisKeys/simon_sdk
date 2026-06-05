from simon import Agent, tool


@tool
def add(a: int, b: int) -> int:
    return a + b


def test_tool_schema_generation() -> None:
    assert add.schema["properties"]["a"]["type"] == "integer"
    assert add.schema["properties"]["b"]["type"] == "integer"


def test_tool_registration_and_call() -> None:
    agent = Agent(tools=[add])
    out = agent.run('tool:add {"a": 2, "b": 3}')
    assert out.text == "5"
