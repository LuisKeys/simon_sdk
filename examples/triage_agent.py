"""Example: a triage agent routes tasks to the right specialist."""

from simon import Agent, TriageAgent

code_agent = Agent(knowledge=False, memory=False)
math_agent = Agent(knowledge=False, memory=False)
writing_agent = Agent(knowledge=False, memory=False)

triage = TriageAgent(
    agents={
        "code": code_agent,
        "math": math_agent,
        "writing": writing_agent,
    },
    descriptions={
        "code": "Handles programming questions, debugging, and code reviews.",
        "math": "Solves mathematical problems, equations, and proofs.",
        "writing": "Helps with essays, creative writing, and editing.",
    },
)

tasks = [
    "Write a Python function that reverses a linked list.",
    "Solve the equation 3x^2 - 12x + 9 = 0.",
    "Write a short poem about the ocean at sunset.",
]

for task in tasks:
    print(f"Task: {task}")
    response = triage.run(task)
    print(f"Response: {response}")
    print()
