from aiogram import Dispatcher

from . import (
    menu,
    mood,
    onboarding,
    profile,
    rating,
    recommendations,
    search,
    soundtrack,
    start,
    wishlist,
)


def setup_routers(dispatcher: Dispatcher) -> None:
    dispatcher.include_router(start.router)
    dispatcher.include_router(onboarding.router)
    dispatcher.include_router(menu.router)
    dispatcher.include_router(search.router)
    dispatcher.include_router(recommendations.router)
    dispatcher.include_router(wishlist.router)
    dispatcher.include_router(profile.router)
    dispatcher.include_router(rating.router)
    dispatcher.include_router(mood.router)
    dispatcher.include_router(soundtrack.router)
