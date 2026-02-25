from enum import StrEnum


class ExperimentStatus(StrEnum):
  CREATED = "created"
  RUNNING = "running"
  ANNOTATING = "annotating"
  COMPLETED = "completed"
  FAILED = "failed"


class RunStatus(StrEnum):
  PENDING = "pending"
  RUNNING = "running"
  COMPLETED = "completed"
  FAILED = "failed"


class PatchAction(StrEnum):
  REPLACE_TEXT = "replace_text"
  SET_ATTRIBUTE = "set_attribute"
  REMOVE_ATTRIBUTE = "remove_attribute"
  ADD_CLASS = "add_class"
  REMOVE_CLASS = "remove_class"
  INSERT_BEFORE = "insert_before"
  INSERT_AFTER = "insert_after"
  REPLACE_ELEMENT = "replace_element"
  REMOVE_ELEMENT = "remove_element"
  APPEND_CHILD = "append_child"
  INJECT_STYLE = "inject_style"
