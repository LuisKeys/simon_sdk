from simon import Agent, JSONFileMemory

# One JSON file == one conversation. Run this script twice: the second run
# remembers what the first run said, because the history lives in the file.
# Open ".simon_chats/robotics_chat.json" to read the stored conversation.
if __name__ == "__main__":
    memory = JSONFileMemory("robotics_chat.json")
    agent = Agent(memory=memory)

    history = agent.run("What did I say my favorite topic is?")
    print(history)

    agent.run("My favorite topic is robotics.")
    print("Saved. Run this script again to see it remembered across runs.")
