from PyQt5.QtWidgets import QCheckBox, QRadioButton


def get_checkboxes[T](*component_value_pairs: tuple[QCheckBox | QRadioButton | bool, T]) -> list[T]:
    """
    根据二值输入组件 (复选框, 单选按钮等) 或布尔值生成值列表

    Args:
        component_value_pairs: 包含 (条件对象或布尔值, 对应值) 的元组

    Returns:
        满足条件的值列表
    """
    result = []
    for condition, value in component_value_pairs:
        if not isinstance(condition, bool):
            condition = condition.isChecked()
        # 如果条件为真，添加对应的值
        if condition:
            result.append(value)
    return result


def get_checkbox[T](component: QCheckBox | QRadioButton, on_value: T = True, off_value: T = False) -> T:
    """
    根据二值输入组件返回开启或关闭的配置值

    Args:
        component: 组件
        on_value: 选中时的值
        off_value: 未选中时的值

    Returns:
        对应的配置值
    """
    return on_value if component.isChecked() else off_value


def get_radio_buttons[T](*radio_mappings: tuple[QRadioButton, T], default: T = "") -> T:
    """
    根据一组单选按钮的选中状态生成配置值

    Args:
        radio_mappings: 包含 (单选按钮对象, 对应配置值) 的元组
        default_value: 当没有单选按钮被选中时的默认值

    Returns:
        选中的单选按钮对应的配置值，如果没有选中则返回默认值
    """
    for radio_button, value in radio_mappings:
        if radio_button.isChecked():
            return value
    return default


def set_radio_buttons[T](value: T, *radio_mappings: tuple[QRadioButton, T], default: QRadioButton | None = None):
    """
    根据配置值设置一组单选按钮的选中状态

    Args:
        value: 配置值
        radio_mappings: 包含 (单选按钮对象, 对应配置值) 的元组
        default_radio: 当没有匹配的配置值时默认选中的单选按钮
    """
    for radio_button, mapping_value in radio_mappings:
        if value == mapping_value:
            radio_button.setChecked(True)
            return

    # 如果没有匹配的值，选中默认单选按钮
    if default:
        default.setChecked(True)


def set_checkboxes[T](value: list[T] | set[T], *checkbox_mappings: tuple[QCheckBox, T]):
    """
    根据配置值设置多个复选框的选中状态

    Args:
        string_value: 配置字符串值
        checkbox_mappings: 包含 (复选框对象, 对应字符串标识) 的元组
    """
    for checkbox, identifier in checkbox_mappings:
        checkbox.setChecked(identifier in value)
