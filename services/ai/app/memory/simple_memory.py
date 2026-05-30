from collections import defaultdict

MAX_HISTORY_MESSAGES = 10

_history: dict[str, list[dict[str, str]]] = defaultdict(list)


def get_history(chat_id: str) -> list[dict[str, str]]:
    return list(_history[chat_id])


def append_message(chat_id: str, role: str, content: str) -> None:
    _history[chat_id].append({"role": role, "content": content})
    trim_history(chat_id)


def trim_history(chat_id: str) -> None:
    if len(_history[chat_id]) > MAX_HISTORY_MESSAGES:
        _history[chat_id] = _history[chat_id][-MAX_HISTORY_MESSAGES:]
