"""Migración inicial: tablas configuracion, operaciones, usuarios

Revision ID: 0001_inicial
Revises:
Create Date: 2026-06-14
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_inicial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "configuracion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("par", sa.String(), server_default="EURUSD"),
        sa.Column("modo", sa.String(), server_default="demo"),
        sa.Column("activo", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("umbral_confianza", sa.Float(), server_default="0.70"),
        sa.Column("max_ops_por_hora", sa.Integer(), server_default="6"),
        sa.Column("monto_porcentaje_balance", sa.Float(), server_default="0.02"),
        sa.Column("perdidas_consecutivas_limite", sa.Integer(), server_default="3"),
        sa.Column("reentrenar_cada_n_ops", sa.Integer(), server_default="100"),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "operaciones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("par", sa.String(), nullable=False),
        sa.Column("direccion", sa.String(), nullable=False),
        sa.Column("monto", sa.Float(), nullable=False),
        sa.Column("resultado", sa.String(), server_default="PENDING"),
        sa.Column("ganancia", sa.Float(), server_default="0"),
        sa.Column("patron_activado", sa.String(), nullable=True),
        sa.Column("confianza_ml", sa.Float(), nullable=True),
        sa.Column("decision_gpt", sa.String(), nullable=True),
        sa.Column("modo", sa.String(), nullable=False),
        sa.Column("indicadores_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_operaciones_created_at", "operaciones", ["created_at"])
    op.create_index("ix_operaciones_modo", "operaciones", ["modo"])

    op.create_table(
        "usuarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("usuarios")
    op.drop_index("ix_operaciones_modo", table_name="operaciones")
    op.drop_index("ix_operaciones_created_at", table_name="operaciones")
    op.drop_table("operaciones")
    op.drop_table("configuracion")
