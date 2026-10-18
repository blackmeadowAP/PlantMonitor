"""Перечисления модели данных (docs/03)."""

import enum


class UserRole(enum.StrEnum):
    worker = "worker"
    agronomist = "agronomist"
    superuser = "superuser"
    admin = "admin"


class PointKind(enum.StrEnum):
    regular = "regular"
    risk = "risk"
    focus = "focus"


class TaskStatus(enum.StrEnum):
    pending = "pending"
    done = "done"
    missed = "missed"


class PhotoKind(enum.StrEnum):
    overview = "overview"
    plant = "plant"
    closeup = "closeup"
    underside = "underside"


class Verdict(enum.StrEnum):
    healthy = "healthy"
    suspect = "suspect"
    disease = "disease"
    reshoot = "reshoot"


class FocusStatus(enum.StrEnum):
    active = "active"
    treated = "treated"
    closed = "closed"


class Trend(enum.StrEnum):
    up = "up"
    flat = "flat"
    down = "down"
