from aiogram.fsm.state import State, StatesGroup


class MoodStates(StatesGroup):
    waiting_preferences = State()
