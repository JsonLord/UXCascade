from __future__ import annotations

import itertools

from app.domain.value_objects.persona import Persona, TraitConfig


class PersonaMatrix:
  """
  Domain service that generates all persona combinations from trait configurations.

  Default trait examples from the paper's experiments:
    Price Sensitivity : budget / flexible
    Time Pressure     : rushed / normal
    Age Cohort        : 18-34 / 55+
    User Type         : new / returning

  Generates agents_per_persona agents for each combination to ensure
  greater behavioral diversity (the paper uses 2 agents per combination).
  """

  AGENTS_PER_PERSONA: int = 2

  def __init__(self, traits: list[TraitConfig]) -> None:
    self._traits = traits

  def generate(self) -> list[Persona]:
    """Returns all trait combinations × agents_per_persona Persona objects."""
    if not self._traits:
      return []

    keys = [t.key for t in self._traits]
    value_lists = [t.values for t in self._traits]

    personas: list[Persona] = []
    for combo in itertools.product(*value_lists):
      trait_dict = dict(zip(keys, combo))
      for _ in range(self.AGENTS_PER_PERSONA):
        personas.append(Persona(traits=trait_dict))

    return personas

  def combination_count(self) -> int:
    """Returns the number of unique trait combinations (not including agent count)."""
    count = 1
    for t in self._traits:
      count *= len(t.values)
    return count
