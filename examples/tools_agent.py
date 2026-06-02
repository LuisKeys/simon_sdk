from simon import Agent, tool


@tool
def weather(city: str) -> str:
    return f"Weather for {city}: sunny"


if __name__ == "__main__":
    agent = Agent(tools=[weather])
    print(agent.run('tool:weather {"city": "Lima"}'))
