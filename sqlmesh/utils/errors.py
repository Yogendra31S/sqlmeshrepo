from __future__ import annotations

import typing as t
from enum import auto
from pathlib import Path

from sqlglot import exp
from sqlglot.helper import AutoName

if t.TYPE_CHECKING:
    from requests.models import Response

    from sqlmesh.core.model import Model


class ErrorLevel(AutoName):
    IGNORE = auto()
    WARN = auto()
    RAISE = auto()


class SQLMeshError(Exception):
    pass


class ConfigError(SQLMeshError):
    pass


class MissingDependencyError(SQLMeshError):
    """Local environment is missing a required dependency for the given operation"""


class MacroEvalError(SQLMeshError):
    pass


class PlanError(SQLMeshError):
    pass


class NoChangesPlanError(PlanError):
    pass


class UncategorizedPlanError(PlanError):
    pass


class ConflictingPlanError(PlanError):
    pass


class MissingContextException(Exception):
    pass


class SnapshotVersionError(SQLMeshError):
    pass


class MagicError(SQLMeshError):
    pass


class AuditConfigError(ConfigError):
    pass


class AuditError(SQLMeshError):
    def __init__(
        self,
        audit_name: str,
        count: int,
        query: exp.Query,
        model: t.Optional[Model] = None,
        # the dialect of the engine adapter that evaluated the audit query
        adapter_dialect: t.Optional[str] = None,
    ) -> None:
        self.audit_name = audit_name
        self.model = model
        self.count = count
        self.query = query
        self.adapter_dialect = adapter_dialect

    def __str__(self) -> str:
        model_str = f" for model '{self.model_name}'" if self.model_name else ""
        return f"Audit '{self.audit_name}'{model_str} failed.\nGot {self.count} results, expected 0.\n{self.sql()}"

    @property
    def model_name(self) -> t.Optional[str]:
        return self.model.name if self.model else None

    def sql(self, dialect: t.Optional[str] = None, **opts: t.Any) -> str:
        """
        Returns the rendered audit query that failed.

        Args:
            dialect: the dialect of the output SQL string, by default,
                     this will use the dialect of the engine adapter that ran the query.
            opts: other `sqlglot.generator.Generator` options.

        Returns:
            The SQL string.
        """
        return self.query.sql(dialect=dialect or self.adapter_dialect, **opts)


class TestError(SQLMeshError):
    __test__ = False  # prevent pytest trying to collect this as a test class
    pass


class NotificationTargetError(SQLMeshError):
    pass


class ApiError(SQLMeshError):
    def __init__(self, message: str, code: int) -> None:
        super().__init__(message)
        self.code = code


class ApiClientError(ApiError):
    pass


class ApiServerError(ApiError):
    pass


class NotFoundError(ApiClientError):
    def __init__(self, message: str) -> None:
        super().__init__(message, 404)


class CICDBotError(SQLMeshError):
    pass


class ParsetimeAdapterCallError(SQLMeshError):
    pass


class EngineAdapterError(SQLMeshError):
    pass


class UnsupportedCatalogOperationError(EngineAdapterError):
    pass


class CircuitBreakerError(SQLMeshError):
    def __init__(self) -> None:
        super().__init__("Circuit breaker triggered.")


class PythonModelEvalError(SQLMeshError):
    pass


def raise_config_error(
    msg: str,
    location: t.Optional[str | Path] = None,
    error_type: t.Type[ConfigError] = ConfigError,
) -> None:
    if location:
        raise error_type(f"{msg} at '{location}'")
    raise error_type(msg)


def raise_for_status(response: Response) -> None:
    if response.status_code == 404:
        raise NotFoundError(response.text)
    if 400 <= response.status_code < 500:
        raise ApiClientError(response.text, response.status_code)
    if 500 <= response.status_code < 600:
        raise ApiServerError(response.text, response.status_code)
