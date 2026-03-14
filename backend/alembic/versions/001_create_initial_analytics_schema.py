"""create initial analytics schema

Revision ID: 001
Revises:
Create Date: 2025-03-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "import_batches",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "raw_meter_readings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("import_batch_id", sa.Integer(), nullable=False),
        sa.Column("source_sheet", sa.String(length=128), nullable=False),
        sa.Column("meter_id", sa.String(length=128), nullable=False),
        sa.Column("meter_type", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=True),
        sa.Column("serial_number", sa.String(length=128), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_value", sa.Float(), nullable=False),
        sa.Column("conversion_factor", sa.Float(), nullable=False),
        sa.Column("obis_code", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["import_batch_id"], ["import_batches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_raw_meter_readings_import_batch_id", "raw_meter_readings", ["import_batch_id"], unique=False)
    op.create_index("ix_raw_meter_readings_meter_id", "raw_meter_readings", ["meter_id"], unique=False)
    op.create_index("ix_raw_meter_readings_meter_type", "raw_meter_readings", ["meter_type"], unique=False)
    op.create_index("ix_raw_meter_readings_tenant_id", "raw_meter_readings", ["tenant_id"], unique=False)
    op.create_index("ix_raw_meter_readings_timestamp", "raw_meter_readings", ["timestamp"], unique=False)

    op.create_table(
        "normalized_meter_readings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("import_batch_id", sa.Integer(), nullable=False),
        sa.Column("meter_id", sa.String(length=128), nullable=False),
        sa.Column("meter_type", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cumulative_kwh", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["import_batch_id"], ["import_batches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_normalized_meter_readings_import_batch_id", "normalized_meter_readings", ["import_batch_id"], unique=False)
    op.create_index("ix_normalized_meter_readings_meter_id", "normalized_meter_readings", ["meter_id"], unique=False)
    op.create_index("ix_normalized_meter_readings_meter_type", "normalized_meter_readings", ["meter_type"], unique=False)
    op.create_index("ix_normalized_meter_readings_tenant_id", "normalized_meter_readings", ["tenant_id"], unique=False)
    op.create_index("ix_normalized_meter_readings_timestamp", "normalized_meter_readings", ["timestamp"], unique=False)

    op.create_table(
        "daily_meter_consumption",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("import_batch_id", sa.Integer(), nullable=False),
        sa.Column("meter_id", sa.String(length=128), nullable=False),
        sa.Column("meter_type", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("delta_kwh", sa.Float(), nullable=False),
        sa.Column("is_valid", sa.Boolean(), nullable=False),
        sa.Column("quality_flag", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["import_batch_id"], ["import_batches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_daily_meter_consumption_date", "daily_meter_consumption", ["date"], unique=False)
    op.create_index("ix_daily_meter_consumption_import_batch_id", "daily_meter_consumption", ["import_batch_id"], unique=False)
    op.create_index("ix_daily_meter_consumption_meter_id", "daily_meter_consumption", ["meter_id"], unique=False)
    op.create_index("ix_daily_meter_consumption_meter_type", "daily_meter_consumption", ["meter_type"], unique=False)
    op.create_index("ix_daily_meter_consumption_tenant_id", "daily_meter_consumption", ["tenant_id"], unique=False)

    op.create_table(
        "daily_energy_sharing",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("import_batch_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("tenant_demand_kwh", sa.Float(), nullable=False),
        sa.Column("allocated_pv_kwh", sa.Float(), nullable=False),
        sa.Column("grid_import_kwh", sa.Float(), nullable=False),
        sa.Column("self_sufficiency_ratio", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["import_batch_id"], ["import_batches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_daily_energy_sharing_date", "daily_energy_sharing", ["date"], unique=False)
    op.create_index("ix_daily_energy_sharing_import_batch_id", "daily_energy_sharing", ["import_batch_id"], unique=False)
    op.create_index("ix_daily_energy_sharing_tenant_id", "daily_energy_sharing", ["tenant_id"], unique=False)

    op.create_table(
        "data_quality_issues",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("import_batch_id", sa.Integer(), nullable=False),
        sa.Column("issue_type", sa.String(length=64), nullable=False),
        sa.Column("meter_id", sa.String(length=128), nullable=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=True),
        sa.Column("date", sa.Date(), nullable=True),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["import_batch_id"], ["import_batches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_data_quality_issues_import_batch_id", "data_quality_issues", ["import_batch_id"], unique=False)
    op.create_index("ix_data_quality_issues_issue_type", "data_quality_issues", ["issue_type"], unique=False)
    op.create_index("ix_data_quality_issues_meter_id", "data_quality_issues", ["meter_id"], unique=False)
    op.create_index("ix_data_quality_issues_tenant_id", "data_quality_issues", ["tenant_id"], unique=False)
    op.create_index("ix_data_quality_issues_date", "data_quality_issues", ["date"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_data_quality_issues_date", table_name="data_quality_issues")
    op.drop_index("ix_data_quality_issues_tenant_id", table_name="data_quality_issues")
    op.drop_index("ix_data_quality_issues_meter_id", table_name="data_quality_issues")
    op.drop_index("ix_data_quality_issues_issue_type", table_name="data_quality_issues")
    op.drop_index("ix_data_quality_issues_import_batch_id", table_name="data_quality_issues")
    op.drop_table("data_quality_issues")
    op.drop_index("ix_daily_energy_sharing_tenant_id", table_name="daily_energy_sharing")
    op.drop_index("ix_daily_energy_sharing_import_batch_id", table_name="daily_energy_sharing")
    op.drop_index("ix_daily_energy_sharing_date", table_name="daily_energy_sharing")
    op.drop_table("daily_energy_sharing")
    op.drop_index("ix_daily_meter_consumption_tenant_id", table_name="daily_meter_consumption")
    op.drop_index("ix_daily_meter_consumption_meter_type", table_name="daily_meter_consumption")
    op.drop_index("ix_daily_meter_consumption_meter_id", table_name="daily_meter_consumption")
    op.drop_index("ix_daily_meter_consumption_import_batch_id", table_name="daily_meter_consumption")
    op.drop_index("ix_daily_meter_consumption_date", table_name="daily_meter_consumption")
    op.drop_table("daily_meter_consumption")
    op.drop_index("ix_normalized_meter_readings_timestamp", table_name="normalized_meter_readings")
    op.drop_index("ix_normalized_meter_readings_tenant_id", table_name="normalized_meter_readings")
    op.drop_index("ix_normalized_meter_readings_meter_type", table_name="normalized_meter_readings")
    op.drop_index("ix_normalized_meter_readings_meter_id", table_name="normalized_meter_readings")
    op.drop_index("ix_normalized_meter_readings_import_batch_id", table_name="normalized_meter_readings")
    op.drop_table("normalized_meter_readings")
    op.drop_index("ix_raw_meter_readings_timestamp", table_name="raw_meter_readings")
    op.drop_index("ix_raw_meter_readings_tenant_id", table_name="raw_meter_readings")
    op.drop_index("ix_raw_meter_readings_meter_type", table_name="raw_meter_readings")
    op.drop_index("ix_raw_meter_readings_meter_id", table_name="raw_meter_readings")
    op.drop_index("ix_raw_meter_readings_import_batch_id", table_name="raw_meter_readings")
    op.drop_table("raw_meter_readings")
    op.drop_table("import_batches")
