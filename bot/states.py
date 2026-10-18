"""Состояния FSM."""

from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    """Регистрация по коду: имя → согласие. Код хранится в данных состояния."""

    name = State()
    consent = State()
