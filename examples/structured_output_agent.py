"""Example: structured output with Pydantic models.

Run:
    python examples/structured_output_agent.py
"""

from pydantic import BaseModel

from simon import Agent


class Recipe(BaseModel):
    title: str
    ingredients: list[str]
    steps: list[str]
    prep_time_minutes: int


agent = Agent(knowledge=False)

response = agent.run(
    "Give me a simple pancake recipe",
    output_model=Recipe,
)

recipe: Recipe = response.parsed
print(f"Recipe: {recipe.title}")
print(f"Prep time: {recipe.prep_time_minutes} minutes")
print(f"Ingredients: {', '.join(recipe.ingredients)}")
print(f"Steps: {len(recipe.steps)} steps")
