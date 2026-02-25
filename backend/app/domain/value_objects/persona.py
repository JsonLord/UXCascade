from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class TraitConfig(BaseModel):
  """Trait configuration. A dimension-value pair used for persona generation."""

  name: str  # e.g. "Price Sensitivity"
  key: str  # e.g. "price_sensitivity"
  values: list[str]  # e.g. ["budget", "flexible"]


class Persona(BaseModel):
  """Persona. An agent personality uniquely identified by a combination of traits."""

  id: str = Field(default_factory=lambda: str(uuid.uuid4()))
  traits: dict[str, str]  # { "price_sensitivity": "budget", ... }

  def to_text(self) -> str:
    """Converts the trait dictionary into a natural language persona description."""
    lines = [f"- {k.replace('_', ' ').title()}: {v}" for k, v in self.traits.items()]
    return "\n".join(lines)

  def __eq__(self, other: object) -> bool:
    if not isinstance(other, Persona):
      return False
    return self.traits == other.traits

  def __hash__(self) -> int:
    return hash(tuple(sorted(self.traits.items())))
