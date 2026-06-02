from simon import Agent

if __name__ == "__main__":
    agent = Agent(memory=True)
    print(agent.run("My favorite topic is robotics."))
    print(agent.run("What did I say my favorite topic is?"))
