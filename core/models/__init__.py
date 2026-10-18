"""SQLAlchemy-модели (docs/03). Импорт всех модулей регистрирует таблицы в Base.metadata."""

from core.models.assessment import AIPrediction, Assessment, Focus, FocusUpdate, Treatment
from core.models.base import Base
from core.models.catalog import Crop, Disease
from core.models.collection import Observation, Photo, Task
from core.models.comms import Message
from core.models.enums import (
    FocusStatus,
    PhotoKind,
    PointKind,
    TaskStatus,
    Trend,
    UserRole,
    Verdict,
)
from core.models.fields import ControlPoint, Field
from core.models.stats import DailyFieldStats, DailyUserStats, Report
from core.models.territory import District, Organization, Region
from core.models.users import Invite, User

__all__ = [
    "AIPrediction",
    "Assessment",
    "Base",
    "ControlPoint",
    "Crop",
    "DailyFieldStats",
    "DailyUserStats",
    "Disease",
    "District",
    "Field",
    "Focus",
    "FocusStatus",
    "FocusUpdate",
    "Invite",
    "Message",
    "Observation",
    "Organization",
    "Photo",
    "PhotoKind",
    "PointKind",
    "Region",
    "Report",
    "Task",
    "TaskStatus",
    "Treatment",
    "Trend",
    "User",
    "UserRole",
    "Verdict",
]
