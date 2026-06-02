from pathlib import Path

from simon import Agent

if __name__ == "__main__":
    tmp_file = Path("knowledge_demo.txt")
    tmp_file.write_text(
        "Reinforcement learning is about agents maximizing reward through interaction.",
        encoding="utf-8",
    )

    agent = Agent()
    agent.knowledge.add(str(tmp_file))
    print(agent.run("What is reinforcement learning about?"))
