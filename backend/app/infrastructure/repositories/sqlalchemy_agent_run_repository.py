from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.experiment import AgentRun
from app.domain.entities.snapshot import EventSnapshot
from app.domain.repositories.agent_run_repository import IAgentRunRepository
from app.domain.value_objects.action import Action, TabMetadata
from app.domain.value_objects.enums import RunStatus
from app.domain.value_objects.persona import Persona
from app.infrastructure.db import models


def _snapshot_row_to_entity(row: models.EventSnapshot) -> EventSnapshot:
  action_data = row.action or {}
  tab_data = row.tab_metadata or {}
  return EventSnapshot(
    agent_run_id=str(row.agent_run_id),
    step=row.step,
    timestamp=row.timestamp,
    raw_html=row.raw_html,
    screenshot=row.screenshot,
    tab_metadata=TabMetadata(
      url=tab_data.get("url", ""),
      title=tab_data.get("title", ""),
    ),
    reasoning=row.reasoning,
    prompt=row.prompt,
    action=Action(
      type=action_data.get("type", "navigate"),
      selector=action_data.get("selector"),
      value=action_data.get("value"),
    ),
    action_result=row.action_result,
    errors=list(row.errors or []),
  )


async def _load_snapshots(
  session: AsyncSession, agent_run_id: Any
) -> list[EventSnapshot]:
  rows = (
    (
      await session.execute(
        select(models.EventSnapshot)
        .where(models.EventSnapshot.agent_run_id == str(agent_run_id))
        .order_by(models.EventSnapshot.step)
      )
    )
    .scalars()
    .all()
  )
  return [_snapshot_row_to_entity(r) for r in rows]


def _run_row_to_entity(
  row: models.AgentRun,
  snapshots: list[EventSnapshot],
) -> AgentRun:
  return AgentRun(
    id=str(row.id),
    experiment_id=str(row.experiment_id),
    persona=Persona(
      id=str(row.persona_id),
      traits=dict(row.persona_traits or {}),
    ),
    goal=row.goal,
    status=RunStatus(row.status),
    success=row.success,
    event_snapshots=snapshots,
    created_at=row.created_at,
    completed_at=row.completed_at,
  )


class SQLAlchemyAgentRunRepository(IAgentRunRepository):
  def __init__(self, session: AsyncSession) -> None:
    self._session = session

  async def save(self, agent_run: AgentRun) -> None:
    run_id = str(agent_run.id)
    row = (
      await self._session.execute(
        select(models.AgentRun).where(models.AgentRun.id == run_id)
      )
    ).scalar_one_or_none()

    if row is None:
      row = models.AgentRun(
        id=run_id,
        experiment_id=str(agent_run.experiment_id),
        persona_id=str(agent_run.persona.id),
        persona_traits=agent_run.persona.traits,
        goal=agent_run.goal,
        status=agent_run.status.value,
        success=agent_run.success,
        completed_at=agent_run.completed_at,
      )
      self._session.add(row)
    else:
      row.status = agent_run.status.value
      row.success = agent_run.success
      row.completed_at = agent_run.completed_at

    await self._session.commit()

  async def find_by_id(self, agent_run_id: str) -> AgentRun | None:
    run_id = str(agent_run_id)
    row = (
      await self._session.execute(
        select(models.AgentRun).where(models.AgentRun.id == run_id)
      )
    ).scalar_one_or_none()
    if row is None:
      return None
    snapshots = await _load_snapshots(self._session, run_id)
    return _run_row_to_entity(row, snapshots)

  async def find_by_experiment_id(self, experiment_id: str) -> list[AgentRun]:
    exp_id = str(experiment_id)
    rows = (
      (
        await self._session.execute(
          select(models.AgentRun).where(models.AgentRun.experiment_id == exp_id)
        )
      )
      .scalars()
      .all()
    )
    result = []
    for row in rows:
      snapshots = await _load_snapshots(self._session, row.id)
      result.append(_run_row_to_entity(row, snapshots))
    return result

  async def append_snapshot(self, agent_run_id: str, snapshot: EventSnapshot) -> None:
    run_id = str(agent_run_id)
    row = models.EventSnapshot(
      agent_run_id=run_id,
      step=snapshot.step,
      timestamp=snapshot.timestamp,
      raw_html=snapshot.raw_html,
      screenshot=snapshot.screenshot,
      tab_metadata={
        "url": snapshot.tab_metadata.url,
        "title": snapshot.tab_metadata.title,
      },
      reasoning=snapshot.reasoning,
      prompt=snapshot.prompt,
      action={
        "type": snapshot.action.type,
        "selector": snapshot.action.selector,
        "value": snapshot.action.value,
      },
      action_result=snapshot.action_result,
      errors=snapshot.errors,
    )
    self._session.add(row)
    await self._session.commit()
