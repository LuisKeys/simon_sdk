from simon import Agent
from simon.tools.builtin import datetime_now, fs_list, fs_read, fs_write, shell_run, web_search

agent = Agent(
    tools=[datetime_now, fs_list, fs_read, fs_write, shell_run, web_search],
    knowledge=False,
)

print("=== datetime_now ===")
print(agent.run("tool:datetime_now {}"))

print("\n=== fs_list (current dir) ===")
print(agent.run('tool:fs_list {"path": "."}'))

print("\n=== fs_write + fs_read ===")
agent.run('tool:fs_write {"path": "/tmp/simon_test.txt", "content": "hello from simon"}')
print(agent.run('tool:fs_read {"path": "/tmp/simon_test.txt"}'))

print("\n=== shell_run ===")
print(agent.run('tool:shell_run {"command": "echo hello from shell"}'))

print("\n=== web_search ===")
print(agent.run('tool:web_search {"query": "python asyncio tutorial"}'))
