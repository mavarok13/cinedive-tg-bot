from aiogram.fsm.state import State, StatesGroup


class RatingStates(StatesGroup):
    waiting_rating = State()
