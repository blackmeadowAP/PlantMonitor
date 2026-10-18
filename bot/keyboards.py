"""Клавиатуры бота."""

from collections.abc import Sequence

from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from bot import texts
from core.models import Organization, Region, UserRole

MENU_ROWS: dict[UserRole, list[list[str]]] = {
    UserRole.worker: [
        [texts.BTN_MY_TASK, texts.BTN_REPORT_PROBLEM],
        [texts.BTN_HOW_TO_SHOOT, texts.BTN_MESSAGE_AGRONOMIST],
    ],
    UserRole.agronomist: [
        [texts.BTN_LABEL_PHOTOS, texts.BTN_ATTENTION],
        [texts.BTN_FIELDS, texts.BTN_FOCI],
        [texts.BTN_WORKERS, texts.BTN_REPORT],
        [texts.BTN_MAP, texts.BTN_INVITE_WORKER],
    ],
    UserRole.superuser: [
        [texts.BTN_REGION_MAP, texts.BTN_SUMMARY],
        [texts.BTN_DOWNLOAD_PDF, texts.BTN_ORGS],
        [texts.BTN_BROADCAST, texts.BTN_INVITE_AGRONOMIST],
    ],
    UserRole.admin: [
        [texts.BTN_CATALOGS, texts.BTN_CREATE_SUPERUSER],
        [texts.BTN_SYSTEM_STATUS],
    ],
}

# Все кнопки меню — для заглушки разделов следующих шагов
ALL_MENU_BUTTONS = frozenset(b for rows in MENU_ROWS.values() for row in rows for b in row)


class ConsentCb(CallbackData, prefix="consent"):
    agree: bool


class InviteOrgCb(CallbackData, prefix="inv_org"):
    org_id: int


class InviteRegionCb(CallbackData, prefix="inv_reg"):
    region_id: int


def main_menu(role: UserRole) -> ReplyKeyboardMarkup:
    """Меню роли (docs/04)."""
    rows = [[KeyboardButton(text=t) for t in row] for row in MENU_ROWS[role]]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, is_persistent=True)


def consent() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=texts.BTN_AGREE, callback_data=ConsentCb(agree=True).pack()
                ),
                InlineKeyboardButton(
                    text=texts.BTN_CANCEL, callback_data=ConsentCb(agree=False).pack()
                ),
            ]
        ]
    )


def choose_org(orgs: Sequence[Organization]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=o.name, callback_data=InviteOrgCb(org_id=o.id).pack())]
            for o in orgs
        ]
    )


def choose_region(regions: Sequence[Region]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=r.name, callback_data=InviteRegionCb(region_id=r.id).pack())]
            for r in regions
        ]
    )
