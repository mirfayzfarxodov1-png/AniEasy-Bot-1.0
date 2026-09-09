RUNTIME_ADMINS: set[int] = set()


def is_admin(uid: int, settings) -> bool:
    return uid in settings.admin_ids or uid == settings.owner_id or uid in RUNTIME_ADMINS


def is_owner(uid: int, settings) -> bool:
    return settings.owner_id is not None and uid == settings.owner_id


def add_admin(uid: int) -> None:
    RUNTIME_ADMINS.add(int(uid))


def remove_admin(uid: int) -> None:
    RUNTIME_ADMINS.discard(int(uid))
