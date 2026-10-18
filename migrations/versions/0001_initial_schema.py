"""Начальная схема: все таблицы docs/03, PostGIS.

Revision ID: 0001
Revises:
Create Date: 2026-10-18 16:33:43.306088
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography
from sqlalchemy.dialects import postgresql

revision: str = '0001'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


ENUM_TYPES = (
    "user_role",
    "point_kind",
    "task_status",
    "photo_kind",
    "verdict",
    "focus_status",
    "trend",
)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.create_table('crops',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_crops'))
    )
    op.create_table('regions',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_regions'))
    )
    op.create_table('reports',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('scope', sa.Text(), nullable=False),
    sa.Column('scope_id', sa.BigInteger(), nullable=False),
    sa.Column('period_from', sa.Date(), nullable=False),
    sa.Column('period_to', sa.Date(), nullable=False),
    sa.Column('s3_key', sa.Text(), nullable=False),
    sa.Column('facts', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('llm_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('facts_hash', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_reports'))
    )
    op.create_table('diseases',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('crop_id', sa.BigInteger(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('latin_name', sa.Text(), nullable=True),
    sa.Column('severity_scale', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('reference_photo_keys', postgresql.ARRAY(sa.Text()), server_default='{}', nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.ForeignKeyConstraint(['crop_id'], ['crops.id'], name=op.f('fk_diseases_crop_id_crops')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_diseases'))
    )
    op.create_index(op.f('ix_diseases_crop_id'), 'diseases', ['crop_id'], unique=False)
    op.create_table('districts',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('region_id', sa.BigInteger(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['region_id'], ['regions.id'], name=op.f('fk_districts_region_id_regions')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_districts'))
    )
    op.create_index(op.f('ix_districts_region_id'), 'districts', ['region_id'], unique=False)
    op.create_geospatial_table('organizations',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('district_id', sa.BigInteger(), nullable=False),
    sa.Column('location', Geography(geometry_type='POINT', srid=4326, dimension=2, spatial_index=False, from_text='ST_GeogFromText', name='geography', nullable=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['district_id'], ['districts.id'], name=op.f('fk_organizations_district_id_districts')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_organizations'))
    )
    op.create_geospatial_index('idx_organizations_location', 'organizations', ['location'], unique=False, postgresql_using='gist', postgresql_ops={})
    op.create_index(op.f('ix_organizations_district_id'), 'organizations', ['district_id'], unique=False)
    op.create_geospatial_table('fields',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('org_id', sa.BigInteger(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('crop_id', sa.BigInteger(), nullable=False),
    sa.Column('area_ha', sa.Numeric(), nullable=False),
    sa.Column('boundary', Geography(geometry_type='POLYGON', srid=4326, dimension=2, spatial_index=False, from_text='ST_GeogFromText', name='geography'), nullable=True),
    sa.Column('centroid', Geography(geometry_type='POINT', srid=4326, dimension=2, spatial_index=False, from_text='ST_GeogFromText', name='geography', nullable=False), nullable=False),
    sa.Column('growth_stage', sa.Text(), nullable=True),
    sa.Column('daily_mode', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.ForeignKeyConstraint(['crop_id'], ['crops.id'], name=op.f('fk_fields_crop_id_crops')),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], name=op.f('fk_fields_org_id_organizations')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_fields'))
    )
    op.create_geospatial_index('idx_fields_boundary', 'fields', ['boundary'], unique=False, postgresql_using='gist', postgresql_ops={})
    op.create_geospatial_index('idx_fields_centroid', 'fields', ['centroid'], unique=False, postgresql_using='gist', postgresql_ops={})
    op.create_index(op.f('ix_fields_org_id'), 'fields', ['org_id'], unique=False)
    op.create_table('users',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('tg_id', sa.BigInteger(), nullable=False),
    sa.Column('full_name', sa.Text(), nullable=False),
    sa.Column('role', sa.Enum('worker', 'agronomist', 'superuser', 'admin', name='user_role'), nullable=False),
    sa.Column('org_id', sa.BigInteger(), nullable=True),
    sa.Column('region_id', sa.BigInteger(), nullable=True),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('consent_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("role <> 'superuser' OR region_id IS NOT NULL", name=op.f('ck_users_region_required')),
    sa.CheckConstraint("role NOT IN ('worker', 'agronomist') OR org_id IS NOT NULL", name=op.f('ck_users_org_required')),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], name=op.f('fk_users_org_id_organizations')),
    sa.ForeignKeyConstraint(['region_id'], ['regions.id'], name=op.f('fk_users_region_id_regions')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users'))
    )
    op.create_index(op.f('ix_users_tg_id'), 'users', ['tg_id'], unique=True)
    op.create_geospatial_table('control_points',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('field_id', sa.BigInteger(), nullable=False),
    sa.Column('location', Geography(geometry_type='POINT', srid=4326, dimension=2, spatial_index=False, from_text='ST_GeogFromText', name='geography', nullable=False), nullable=False),
    sa.Column('kind', sa.Enum('regular', 'risk', 'focus', name='point_kind'), nullable=False),
    sa.Column('assigned_user_id', sa.BigInteger(), nullable=True),
    sa.Column('interval_days', sa.Integer(), server_default=sa.text('3'), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['assigned_user_id'], ['users.id'], name=op.f('fk_control_points_assigned_user_id_users')),
    sa.ForeignKeyConstraint(['field_id'], ['fields.id'], name=op.f('fk_control_points_field_id_fields')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_control_points'))
    )
    op.create_geospatial_index('idx_control_points_location', 'control_points', ['location'], unique=False, postgresql_using='gist', postgresql_ops={})
    op.create_index(op.f('ix_control_points_assigned_user_id'), 'control_points', ['assigned_user_id'], unique=False)
    op.create_index(op.f('ix_control_points_field_id'), 'control_points', ['field_id'], unique=False)
    op.create_table('daily_field_stats',
    sa.Column('field_id', sa.BigInteger(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('prevalence_pct', sa.Numeric(), nullable=True),
    sa.Column('severity_avg', sa.Numeric(), nullable=True),
    sa.Column('speed_pp_day', sa.Numeric(), nullable=True),
    sa.Column('trend', sa.Enum('up', 'flat', 'down', name='trend'), nullable=True),
    sa.Column('n_observations', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('last_photo_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['field_id'], ['fields.id'], name=op.f('fk_daily_field_stats_field_id_fields')),
    sa.PrimaryKeyConstraint('field_id', 'date', name=op.f('pk_daily_field_stats'))
    )
    op.create_table('daily_user_stats',
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('tasks_total', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('tasks_done', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('photos', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('photos_ok', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('avg_distance_m', sa.Numeric(), nullable=True),
    sa.Column('unplanned', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_daily_user_stats_user_id_users')),
    sa.PrimaryKeyConstraint('user_id', 'date', name=op.f('pk_daily_user_stats'))
    )
    op.create_table('invites',
    sa.Column('code', sa.Text(), nullable=False),
    sa.Column('role', sa.Enum('worker', 'agronomist', 'superuser', 'admin', name='user_role'), nullable=False),
    sa.Column('org_id', sa.BigInteger(), nullable=True),
    sa.Column('region_id', sa.BigInteger(), nullable=True),
    sa.Column('created_by', sa.BigInteger(), nullable=True),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('used_by', sa.BigInteger(), nullable=True),
    sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], name=op.f('fk_invites_created_by_users')),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], name=op.f('fk_invites_org_id_organizations')),
    sa.ForeignKeyConstraint(['region_id'], ['regions.id'], name=op.f('fk_invites_region_id_regions')),
    sa.ForeignKeyConstraint(['used_by'], ['users.id'], name=op.f('fk_invites_used_by_users')),
    sa.PrimaryKeyConstraint('code', name=op.f('pk_invites'))
    )
    op.create_table('messages',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('from_user', sa.BigInteger(), nullable=False),
    sa.Column('to_user', sa.BigInteger(), nullable=True),
    sa.Column('scope', sa.Text(), nullable=True),
    sa.Column('ref_type', sa.Text(), nullable=True),
    sa.Column('ref_id', sa.BigInteger(), nullable=True),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['from_user'], ['users.id'], name=op.f('fk_messages_from_user_users')),
    sa.ForeignKeyConstraint(['to_user'], ['users.id'], name=op.f('fk_messages_to_user_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_messages'))
    )
    op.create_index(op.f('ix_messages_from_user'), 'messages', ['from_user'], unique=False)
    op.create_index(op.f('ix_messages_to_user'), 'messages', ['to_user'], unique=False)
    op.create_geospatial_table('foci',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('field_id', sa.BigInteger(), nullable=False),
    sa.Column('disease_id', sa.BigInteger(), nullable=False),
    sa.Column('point_id', sa.BigInteger(), nullable=True),
    sa.Column('location', Geography(geometry_type='POINT', srid=4326, dimension=2, spatial_index=False, from_text='ST_GeogFromText', name='geography', nullable=False), nullable=False),
    sa.Column('area_ha', sa.Numeric(), nullable=True),
    sa.Column('status', sa.Enum('active', 'treated', 'closed', name='focus_status'), nullable=False),
    sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], name=op.f('fk_foci_created_by_users')),
    sa.ForeignKeyConstraint(['disease_id'], ['diseases.id'], name=op.f('fk_foci_disease_id_diseases')),
    sa.ForeignKeyConstraint(['field_id'], ['fields.id'], name=op.f('fk_foci_field_id_fields')),
    sa.ForeignKeyConstraint(['point_id'], ['control_points.id'], name=op.f('fk_foci_point_id_control_points')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_foci'))
    )
    op.create_geospatial_index('idx_foci_location', 'foci', ['location'], unique=False, postgresql_using='gist', postgresql_ops={})
    op.create_index('ix_foci_field_id_status', 'foci', ['field_id', 'status'], unique=False)
    op.create_table('tasks',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('point_id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('status', sa.Enum('pending', 'done', 'missed', name='task_status'), server_default='pending', nullable=False),
    sa.Column('done_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['point_id'], ['control_points.id'], name=op.f('fk_tasks_point_id_control_points')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_tasks_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_tasks')),
    sa.UniqueConstraint('point_id', 'date', name='uq_tasks_point_id_date')
    )
    op.create_index('ix_tasks_date_status', 'tasks', ['date', 'status'], unique=False)
    op.create_index('ix_tasks_user_id_date', 'tasks', ['user_id', 'date'], unique=False)
    op.create_table('focus_updates',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('focus_id', sa.BigInteger(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('prevalence_pct', sa.Numeric(), nullable=False),
    sa.Column('severity', sa.Numeric(), nullable=True),
    sa.Column('note', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['focus_id'], ['foci.id'], name=op.f('fk_focus_updates_focus_id_foci')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_focus_updates'))
    )
    op.create_index(op.f('ix_focus_updates_focus_id'), 'focus_updates', ['focus_id'], unique=False)
    op.create_geospatial_table('observations',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('task_id', sa.BigInteger(), nullable=True),
    sa.Column('point_id', sa.BigInteger(), nullable=True),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('location', Geography(geometry_type='POINT', srid=4326, dimension=2, spatial_index=False, from_text='ST_GeogFromText', name='geography', nullable=False), nullable=False),
    sa.Column('distance_m', sa.Numeric(), nullable=True),
    sa.Column('taken_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('plants_inspected', sa.Integer(), server_default=sa.text('10'), nullable=False),
    sa.Column('plants_affected', sa.Integer(), nullable=False),
    sa.Column('wet_leaves', sa.Boolean(), nullable=False),
    sa.Column('is_unplanned', sa.Boolean(), nullable=False),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['point_id'], ['control_points.id'], name=op.f('fk_observations_point_id_control_points')),
    sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], name=op.f('fk_observations_task_id_tasks')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_observations_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_observations'))
    )
    op.create_geospatial_index('idx_observations_location', 'observations', ['location'], unique=False, postgresql_using='gist', postgresql_ops={})
    op.create_index('ix_observations_point_id_taken_at', 'observations', ['point_id', 'taken_at'], unique=False)
    op.create_index(op.f('ix_observations_task_id'), 'observations', ['task_id'], unique=False)
    op.create_index(op.f('ix_observations_user_id'), 'observations', ['user_id'], unique=False)
    op.create_table('treatments',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('field_id', sa.BigInteger(), nullable=False),
    sa.Column('focus_id', sa.BigInteger(), nullable=True),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('product', sa.Text(), nullable=False),
    sa.Column('rate', sa.Text(), nullable=False),
    sa.Column('area_ha', sa.Numeric(), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], name=op.f('fk_treatments_created_by_users')),
    sa.ForeignKeyConstraint(['field_id'], ['fields.id'], name=op.f('fk_treatments_field_id_fields')),
    sa.ForeignKeyConstraint(['focus_id'], ['foci.id'], name=op.f('fk_treatments_focus_id_foci')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_treatments'))
    )
    op.create_index(op.f('ix_treatments_field_id'), 'treatments', ['field_id'], unique=False)
    op.create_table('assessments',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('observation_id', sa.BigInteger(), nullable=False),
    sa.Column('agronomist_id', sa.BigInteger(), nullable=False),
    sa.Column('verdict', sa.Enum('healthy', 'suspect', 'disease', 'reshoot', name='verdict'), nullable=False),
    sa.Column('disease_id', sa.BigInteger(), nullable=True),
    sa.Column('severity', sa.Integer(), nullable=True),
    sa.Column('confirmed_on_site', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['agronomist_id'], ['users.id'], name=op.f('fk_assessments_agronomist_id_users')),
    sa.ForeignKeyConstraint(['disease_id'], ['diseases.id'], name=op.f('fk_assessments_disease_id_diseases')),
    sa.ForeignKeyConstraint(['observation_id'], ['observations.id'], name=op.f('fk_assessments_observation_id_observations')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_assessments'))
    )
    op.create_index('ix_assessments_observation_id_created_at', 'assessments', ['observation_id', sa.literal_column('created_at DESC')], unique=False)
    op.create_table('photos',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('observation_id', sa.BigInteger(), nullable=False),
    sa.Column('kind', sa.Enum('overview', 'plant', 'closeup', 'underside', name='photo_kind'), nullable=False),
    sa.Column('s3_key', sa.Text(), nullable=True),
    sa.Column('tg_file_id', sa.Text(), nullable=False),
    sa.Column('tg_file_unique_id', sa.Text(), nullable=False),
    sa.Column('archive_msg_id', sa.BigInteger(), nullable=True),
    sa.Column('width', sa.Integer(), nullable=False),
    sa.Column('height', sa.Integer(), nullable=False),
    sa.Column('blur_score', sa.Float(), nullable=False),
    sa.Column('brightness', sa.Float(), nullable=False),
    sa.Column('quality_ok', sa.Boolean(), nullable=False),
    sa.Column('keep_forever', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['observation_id'], ['observations.id'], name=op.f('fk_photos_observation_id_observations')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_photos'))
    )
    op.create_index(op.f('ix_photos_observation_id'), 'photos', ['observation_id'], unique=False)
    op.create_table('ai_predictions',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('photo_id', sa.BigInteger(), nullable=False),
    sa.Column('model_version', sa.Text(), nullable=False),
    sa.Column('top1_disease_id', sa.BigInteger(), nullable=True),
    sa.Column('top1_label', sa.Text(), nullable=False),
    sa.Column('top1_prob', sa.Float(), nullable=False),
    sa.Column('top3', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['photo_id'], ['photos.id'], name=op.f('fk_ai_predictions_photo_id_photos')),
    sa.ForeignKeyConstraint(['top1_disease_id'], ['diseases.id'], name=op.f('fk_ai_predictions_top1_disease_id_diseases')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_ai_predictions'))
    )
    op.create_index(op.f('ix_ai_predictions_photo_id'), 'ai_predictions', ['photo_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ai_predictions_photo_id'), table_name='ai_predictions')
    op.drop_table('ai_predictions')
    op.drop_index(op.f('ix_photos_observation_id'), table_name='photos')
    op.drop_table('photos')
    op.drop_index('ix_assessments_observation_id_created_at', table_name='assessments')
    op.drop_table('assessments')
    op.drop_index(op.f('ix_treatments_field_id'), table_name='treatments')
    op.drop_table('treatments')
    op.drop_index(op.f('ix_observations_user_id'), table_name='observations')
    op.drop_index(op.f('ix_observations_task_id'), table_name='observations')
    op.drop_index('ix_observations_point_id_taken_at', table_name='observations')
    op.drop_geospatial_index('idx_observations_location', table_name='observations', postgresql_using='gist', column_name='location')
    op.drop_geospatial_table('observations')
    op.drop_index(op.f('ix_focus_updates_focus_id'), table_name='focus_updates')
    op.drop_table('focus_updates')
    op.drop_index('ix_tasks_user_id_date', table_name='tasks')
    op.drop_index('ix_tasks_date_status', table_name='tasks')
    op.drop_table('tasks')
    op.drop_index('ix_foci_field_id_status', table_name='foci')
    op.drop_geospatial_index('idx_foci_location', table_name='foci', postgresql_using='gist', column_name='location')
    op.drop_geospatial_table('foci')
    op.drop_index(op.f('ix_messages_to_user'), table_name='messages')
    op.drop_index(op.f('ix_messages_from_user'), table_name='messages')
    op.drop_table('messages')
    op.drop_table('invites')
    op.drop_table('daily_user_stats')
    op.drop_table('daily_field_stats')
    op.drop_index(op.f('ix_control_points_field_id'), table_name='control_points')
    op.drop_index(op.f('ix_control_points_assigned_user_id'), table_name='control_points')
    op.drop_geospatial_index('idx_control_points_location', table_name='control_points', postgresql_using='gist', column_name='location')
    op.drop_geospatial_table('control_points')
    op.drop_index(op.f('ix_users_tg_id'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_fields_org_id'), table_name='fields')
    op.drop_geospatial_index('idx_fields_centroid', table_name='fields', postgresql_using='gist', column_name='centroid')
    op.drop_geospatial_index('idx_fields_boundary', table_name='fields', postgresql_using='gist', column_name='boundary')
    op.drop_geospatial_table('fields')
    op.drop_index(op.f('ix_organizations_district_id'), table_name='organizations')
    op.drop_geospatial_index('idx_organizations_location', table_name='organizations', postgresql_using='gist', column_name='location')
    op.drop_geospatial_table('organizations')
    op.drop_index(op.f('ix_districts_region_id'), table_name='districts')
    op.drop_table('districts')
    op.drop_index(op.f('ix_diseases_crop_id'), table_name='diseases')
    op.drop_table('diseases')
    op.drop_table('reports')
    op.drop_table('regions')
    op.drop_table('crops')
    for name in ENUM_TYPES:
        op.execute(f"DROP TYPE IF EXISTS {name}")
    # Расширение postgis не удаляем: от него могут зависеть другие объекты БД
