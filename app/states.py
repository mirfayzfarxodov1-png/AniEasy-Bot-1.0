from aiogram.fsm.state import State, StatesGroup

class AddAnime(StatesGroup):
    title = State()

class Upload(StatesGroup):
    episodes = State()
    manual_number = State()

class Search(StatesGroup):
    query = State()

class Broadcast(StatesGroup):
    text = State()

class EditAnime(StatesGroup):
    field = State()
    value = State()

class AdminManage(StatesGroup):
    add_id = State()
    remove_id = State()
