from ..config.manager import manager
from ..number import remove_escape_string1


def remove_escape_string(filename: str, replace_char: str = "") -> str:
    return remove_escape_string1(filename, manager.computed.escape_string_list, replace_char)


def deal_actor_more(actor: str) -> str:
    actor_name_max = int(manager.config.actor_name_max)
    actor_name_more = manager.config.actor_name_more
    actor_list = actor.split(",")
    if len(actor_list) > actor_name_max:  # 演员多于设置值时
        actor = ""
        for i in range(actor_name_max):
            actor = actor + actor_list[i] + ","
        actor = actor.strip(",") + actor_name_more
    return actor
