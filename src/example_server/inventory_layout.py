"""Column selection and adaptation for supported inventory layouts."""

from collections.abc import Callable
from dataclasses import dataclass

from example_server.legacy_project_adapter import prepare_legacy_project
from example_server.project_reader import prepare_project


@dataclass(frozen=True)
class InventoryLayout:
    """Trusted SQL expressions and the corresponding record adapter."""

    select_columns: str
    id_expression: str
    prepare_record: Callable[[dict], dict]


def _prepare_legacy_record(record: dict) -> dict:
    return prepare_legacy_project(
        record,
        entry_id=record["entry_id"],
    ).model_dump()


def get_inventory_layout(dataset_format: str) -> InventoryLayout:
    """Select an explicit layout without inferring it from a table name."""
    if dataset_format == "mock":
        return InventoryLayout(
            select_columns="""
                CAST(id AS STRING) AS entry_id,
                agency,
                organization,
                name,
                description,
                repositoryURL,
                version,
                usageType,
                licenses,
                tags,
                languages,
                laborHours,
                dateCreated,
                dateLastModified,
                dateMetadataLastUpdated
            """,
            id_expression="CAST(id AS STRING)",
            prepare_record=prepare_project,
        )

    if dataset_format == "legacy":
        return InventoryLayout(
            select_columns="""
                entry_id,
                agency,
                organization,
                name,
                description,
                repositoryURL,
                permissions_usageType,
                permissions_licenses,
                tags,
                languages,
                laborHours,
                date_created,
                date_lastModified
            """,
            id_expression="entry_id",
            prepare_record=_prepare_legacy_record,
        )

    raise ValueError("dataset_format must be mock or legacy")
