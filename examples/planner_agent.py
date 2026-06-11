"""Planner example: decompose a goal into tasks and run each one.

The checklist prints after every status change, so you watch tasks move from
pending (○) to in-progress (◐) to done (✓).
"""

from simon import Agent, Planner

planner = Planner(agent=Agent(knowledge=False))
tasks = planner.run("Plan a short blog post about why Python is great for beginners")

print("\nResults:")
for task in tasks:
    print(f"- {task.description}\n  {task.result}\n")
