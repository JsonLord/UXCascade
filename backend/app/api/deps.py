from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.database import get_session
from app.infrastructure.repositories.sqlalchemy_agent_run_repository import (
  SQLAlchemyAgentRunRepository,
)
from app.infrastructure.repositories.sqlalchemy_annotation_repository import (
  SQLAlchemyAnnotationRepository,
)
from app.infrastructure.repositories.sqlalchemy_experiment_repository import (
  SQLAlchemyExperimentRepository,
)
from app.infrastructure.repositories.sqlalchemy_fix_repository import (
  SQLAlchemyFixRepository,
)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_experiment_repo(session: SessionDep) -> SQLAlchemyExperimentRepository:
  return SQLAlchemyExperimentRepository(session)


def get_agent_run_repo(session: SessionDep) -> SQLAlchemyAgentRunRepository:
  return SQLAlchemyAgentRunRepository(session)


def get_fix_repo(session: SessionDep) -> SQLAlchemyFixRepository:
  return SQLAlchemyFixRepository(session)


def get_annotation_repo(session: SessionDep) -> SQLAlchemyAnnotationRepository:
  return SQLAlchemyAnnotationRepository(session)


def get_refinement_service(
  agent_run_repo: Annotated[SQLAlchemyAgentRunRepository, Depends(get_agent_run_repo)],
  fix_repo: Annotated[SQLAlchemyFixRepository, Depends(get_fix_repo)],
):
  from app.agents.editor_agent import EditorAgent
  from app.agents.preview_agent import PreviewAgent
  from app.application.services.refinement_service import RefinementService
  from app.infrastructure.browser_adapter import BrowserUseAdapter

  return RefinementService(
    editor_agent=EditorAgent(),
    preview_agent=PreviewAgent(browser_port=BrowserUseAdapter()),
    agent_run_repo=agent_run_repo,
    fix_repo=fix_repo,
  )
