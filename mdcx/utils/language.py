import re

# https://www.compart.com/en/unicode/plane/U+0000
# 暂不考虑扩展假名
KANA = re.compile(r"[\u3040-\u30FF]")

# 仅包含英文字母, 数字, 常用标点符号和空格
MAYBE_EN = re.compile(r"^[a-zA-Z0-9\s.,;:!?()\-\"'`~@#$%^&*+=_/\\|<>]+$")


def is_japanese(s: str) -> bool:
    return bool(KANA.search(s))


def is_english(s: str) -> bool:
    return bool(MAYBE_EN.match(s))
