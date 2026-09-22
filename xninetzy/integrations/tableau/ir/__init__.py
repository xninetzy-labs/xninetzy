from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from xninetzy.integrations.tableau.errors import TableauIntegrationError


WORKBOOK_NS = "http://www.tableausoftware.com/xml/user"

_TYPED_DATATYPES = frozenset({"integer", "real", "string", "boolean", "date", "datetime"})


@dataclass(slots=True)
class SchemaColumn:
    name: str
    caption: str = ""
    datatype: str = "string"
    role: str = "dimension"
    semantic_role: str | None = None
    null_count: int = 0
    unique_count: int = 0
    sample: list[Any] = field(default_factory=list)

    def is_numeric(self) -> bool:
        return self.datatype in {"integer", "real"}

    def is_temporal(self) -> bool:
        return self.datatype in {"date", "datetime"}


@dataclass(slots=True)
class DatasetProfile:
    source_path: str
    row_count: int
    column_count: int
    columns: list[SchemaColumn] = field(default_factory=list)
    duplicate_columns: list[str] = field(default_factory=list)
    inferred_at: float = field(default_factory=lambda: time.time())

    def measure_columns(self) -> list[SchemaColumn]:
        return [c for c in self.columns if c.is_numeric() or c.role == "measure"]

    def dimension_columns(self) -> list[SchemaColumn]:
        return [c for c in self.columns if c.role == "dimension" and not c.is_numeric()]

    def temporal_columns(self) -> list[SchemaColumn]:
        return [c for c in self.columns if c.is_temporal()]

    def to_dict(self) -> dict:
        return {
            "source_path": self.source_path,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "duplicate_columns": list(self.duplicate_columns),
            "columns": [
                {
                    "name": c.name,
                    "caption": c.caption,
                    "datatype": c.datatype,
                    "role": c.role,
                    "null_count": c.null_count,
                    "unique_count": c.unique_count,
                    "sample": c.sample[:3],
                }
                for c in self.columns
            ],
            "measures": [c.name for c in self.measure_columns()],
            "dimensions": [c.name for c in self.dimension_columns()],
            "temporal": [c.name for c in self.temporal_columns()],
        }


@dataclass(slots=True)
class HyperExtractRecord:
    extract_path: str
    schema_hash: str
    row_count: int
    columns: list[SchemaColumn] = field(default_factory=list)
    created_at: float = field(default_factory=lambda: time.time())
    size_bytes: int = 0

    def to_dict(self) -> dict:
        return {
            "extract_path": self.extract_path,
            "schema_hash": self.schema_hash,
            "row_count": self.row_count,
            "size_bytes": self.size_bytes,
            "column_count": len(self.columns),
            "columns": [c.name for c in self.columns],
        }


@dataclass(slots=True)
class PublishTarget:
    server_url: str
    site_id: str = ""
    project: str = "default"
    token_name: str = ""
    token_secret: str = ""

    def safe_dict(self) -> dict:
        return {
            "server_url": self.server_url,
            "site_id": self.site_id,
            "project": self.project,
            "token_name": self.token_name,
        }


@dataclass(slots=True)
class PublishResult:
    workbook_id: str = ""
    workbook_url: str = ""
    status: str = "pending"
    published_at: float = field(default_factory=lambda: time.time())
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "workbook_id": self.workbook_id,
            "workbook_url": self.workbook_url,
            "status": self.status,
            "published_at": self.published_at,
            "error": self.error,
        }


@dataclass(slots=True)
class ArtifactRecord:
    artifact_id: str
    path: str
    kind: str
    state: str = "GENERATING"
    schema_hash: str = ""
    workbook_id: str = ""
    validation: str = ""
    created_at: float = field(default_factory=lambda: time.time())

    def to_dict(self) -> dict:
        return {
            "artifact_id": self.artifact_id,
            "path": self.path,
            "kind": self.kind,
            "state": self.state,
            "schema_hash": self.schema_hash,
            "workbook_id": self.workbook_id,
            "validation": self.validation,
            "created_at": self.created_at,
        }


def _stable_hash(parts: tuple[Any, ...]) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(str(p).encode("utf-8", errors="replace"))
        h.update(b"|")
    return h.hexdigest()[:16]


def _datasource_equivalent(a: Datasource, b: Datasource) -> bool:
    if a.connection_class != b.connection_class:
        return False
    if a.connection_path != b.connection_path:
        return False
    if a.connection_directory != b.connection_directory:
        return False
    a_fields = [(f.name, f.datatype, f.role) for f in a.fields]
    b_fields = [(f.name, f.datatype, f.role) for f in b.fields]
    return a_fields == b_fields


@dataclass(slots=True)
class WorkbookMetadata:
    source_platform: str = "linux"
    source_build: str = "2026.2.1"
    original_version: str = "18.1"
    version: str = "18.1"

    @classmethod
    def from_root(cls, root) -> "WorkbookMetadata":
        return cls(
            source_platform=str(root.get("source-platform", "linux")).lower(),
            source_build=str(root.get("source-build", "")),
            original_version=str(root.get("original-version", "18.1")),
            version=str(root.get("version", "18.1")),
        )


@dataclass(slots=True)
class DatasourceField:
    name: str
    caption: str = ""
    datatype: str = "string"
    role: str = "dimension"
    semantic_role: str | None = None


@dataclass(slots=True)
class Datasource:
    name: str
    caption: str = ""
    connection_class: str = "textscan"
    connection_path: str = ""
    connection_directory: str = ""
    fields: list[DatasourceField] = field(default_factory=list)
    raw_xml: str = ""

    def field_captions(self) -> list[str]:
        return [f.caption or f.name for f in self.fields]


@dataclass(slots=True)
class Worksheet:
    name: str
    title: str = ""
    mark_class: str = "Automatic"
    raw_xml: str = ""


@dataclass(slots=True)
class Dashboard:
    name: str
    is_storyboard: bool = False
    raw_xml: str = ""


@dataclass(slots=True)
class VisualizationSpec:
    type: str
    rows: list[str] = field(default_factory=list)
    cols: list[str] = field(default_factory=list)
    measure: str | None = None
    measure_aggregation: str = "SUM"
    color: str | None = None
    size: str | None = None
    label: str | None = None
    top_n: int | None = None
    trend_line: bool = False

    def mark_class(self) -> str:
        table = {
            "bar": "Bar",
            "line": "Line",
            "area": "Area",
            "circle": "Circle",
            "square": "Square",
            "map": "FilledMap",
            "kpi": "Text",
            "pie": "Pie",
            "scatter": "Circle",
            "heatmap": "Square",
            "table": "Text",
        }
        return table.get(self.type.lower(), "Automatic")


@dataclass(slots=True)
class Workbook:
    metadata: WorkbookMetadata
    datasources: list[Datasource] = field(default_factory=list)
    worksheets: list[Worksheet] = field(default_factory=list)
    dashboards: list[Dashboard] = field(default_factory=list)
    worksheets_xml: dict[str, str] = field(default_factory=dict)
    dashboards_xml: dict[str, str] = field(default_factory=dict)
    datasource_xml: dict[str, str] = field(default_factory=dict)
    _datasource_index: dict[str, int] = field(default_factory=dict)
    preferences_xml: str = ""
    document_format_xml: str = ""
    manifest_changes_xml: str = ""
    story_points: list[tuple[str, str]] = field(default_factory=list)
    source_path: Optional[Path] = None

    def add_datasource(self, ds: Datasource) -> None:
        existing = self._datasource_index.get(ds.name)
        if existing is not None:
            current = self.datasources[existing]
            if not _datasource_equivalent(current, ds):
                raise TableauIntegrationError(
                    f"DATASOURCE_DUPLICATE: '{ds.name}' already exists with different schema",
                    code="DATASOURCE_DUPLICATE",
                )
            return
        self._datasource_index[ds.name] = len(self.datasources)
        self.datasources.append(ds)

    def get_datasource(self, name: str) -> Optional[Datasource]:
        idx = self._datasource_index.get(name)
        if idx is None:
            return None
        return self.datasources[idx]

    def datasource_names(self) -> list[str]:
        return [d.name for d in self.datasources]

    def worksheet_names(self) -> list[str]:
        return [w.name for w in self.worksheets]

    def dashboard_names(self) -> list[str]:
        return [d.name for d in self.dashboards]

    def add_worksheet(self, name: str, spec: VisualizationSpec) -> None:
        if any(w.name == name for w in self.worksheets):
            raise TableauIntegrationError(
                f"Worksheet '{name}' already exists", code="WORKSHEET_CONFLICT"
            )

    def to_dict(self) -> dict:
        return {
            "metadata": {
                "source_platform": self.metadata.source_platform,
                "source_build": self.metadata.source_build,
                "version": self.metadata.version,
            },
            "datasources": [d.name for d in self.datasources],
            "worksheets": [w.name for w in self.worksheets],
            "dashboards": [d.name for d in self.dashboards],
            "story_points": [s[0] for s in self.story_points],
        }


__all__ = [
    "WORKBOOK_NS",
    "WorkbookMetadata",
    "DatasourceField",
    "Datasource",
    "Worksheet",
    "Dashboard",
    "VisualizationSpec",
    "Workbook",
    "SchemaColumn",
    "DatasetProfile",
    "HyperExtractRecord",
    "PublishTarget",
    "PublishResult",
    "ArtifactRecord",
]
