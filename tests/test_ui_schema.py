"""
测试 UI Schema 提取功能
"""

from mdcx.config.ui_schema import extract_ui_schema_recursive


class TestExtractUISchemaRecursive:
    """测试 extract_ui_schema_recursive 函数"""

    def test_empty_schema(self):
        """测试空 schema"""
        result = extract_ui_schema_recursive({})
        assert result == {}

    def test_schema_without_ui_info(self):
        """测试没有 UI 信息的 schema"""
        schema = {"type": "string", "title": "Test Field"}
        result = extract_ui_schema_recursive(schema)
        assert result == {}

    def test_direct_ui_schema(self):
        """测试直接包含 uiSchema 的情况"""
        schema = {"type": "string", "uiSchema": {"ui:widget": "textarea", "ui:placeholder": "Enter text here"}}
        expected = {"ui:widget": "textarea", "ui:placeholder": "Enter text here"}
        result = extract_ui_schema_recursive(schema)
        assert result == expected

    def test_object_with_properties(self):
        """测试包含 properties 的对象类型"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "uiSchema": {"ui:widget": "text"}},
                "age": {"type": "number", "uiSchema": {"ui:widget": "updown"}},
                "description": {
                    "type": "string"
                    # 没有 uiSchema
                },
            },
        }
        expected = {
            "name": {"ui:widget": "text"},
            "age": {"ui:widget": "updown"},
            # description 不应出现，因为没有 UI schema
        }
        result = extract_ui_schema_recursive(schema)
        assert result == expected

    def test_object_with_ui_schema_and_properties(self):
        """测试既有 uiSchema 又有 properties 的对象"""
        schema = {
            "type": "object",
            "uiSchema": {"ui:order": ["name", "age"]},
            "properties": {
                "name": {"type": "string", "uiSchema": {"ui:widget": "text"}},
                "age": {"type": "number", "uiSchema": {"ui:widget": "updown"}},
            },
        }
        expected = {"ui:order": ["name", "age"], "name": {"ui:widget": "text"}, "age": {"ui:widget": "updown"}}
        result = extract_ui_schema_recursive(schema)
        assert result == expected

    def test_array_with_items(self):
        """测试数组类型的 schema"""
        schema = {"type": "array", "items": {"type": "string", "uiSchema": {"ui:widget": "textarea"}}}
        expected = {"items": {"ui:widget": "textarea"}}
        result = extract_ui_schema_recursive(schema)
        assert result == expected

    def test_array_with_ui_schema_and_items(self):
        """测试既有 uiSchema 又有 items 的数组"""
        schema = {
            "type": "array",
            "uiSchema": {"ui:options": {"addable": True, "removable": True}},
            "items": {"type": "string", "uiSchema": {"ui:widget": "textarea"}},
        }
        expected = {"ui:options": {"addable": True, "removable": True}, "items": {"ui:widget": "textarea"}}
        result = extract_ui_schema_recursive(schema)
        assert result == expected

    def test_nested_objects(self):
        """测试嵌套对象"""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "uiSchema": {"ui:title": "User Info"},
                    "properties": {
                        "profile": {
                            "type": "object",
                            "properties": {"name": {"type": "string", "uiSchema": {"ui:widget": "text"}}},
                        }
                    },
                }
            },
        }
        expected = {"user": {"ui:title": "User Info", "profile": {"name": {"ui:widget": "text"}}}}
        result = extract_ui_schema_recursive(schema)
        assert result == expected

    def test_array_of_objects(self):
        """测试对象数组"""
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "uiSchema": {"ui:title": "Item"},
                "properties": {"name": {"type": "string", "uiSchema": {"ui:widget": "text"}}},
            },
        }
        expected = {"items": {"ui:title": "Item", "name": {"ui:widget": "text"}}}
        result = extract_ui_schema_recursive(schema)
        assert result == expected

    def test_complex_nested_structure(self):
        """测试复杂的嵌套结构"""
        schema = {
            "type": "object",
            "uiSchema": {"ui:title": "Root"},
            "properties": {
                "settings": {
                    "type": "object",
                    "properties": {
                        "notifications": {
                            "type": "array",
                            "uiSchema": {"ui:options": {"orderable": False}},
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string", "uiSchema": {"ui:widget": "select"}},
                                    "enabled": {"type": "boolean", "uiSchema": {"ui:widget": "checkbox"}},
                                },
                            },
                        }
                    },
                }
            },
        }
        expected = {
            "ui:title": "Root",
            "settings": {
                "notifications": {
                    "ui:options": {"orderable": False},
                    "items": {"type": {"ui:widget": "select"}, "enabled": {"ui:widget": "checkbox"}},
                }
            },
        }
        result = extract_ui_schema_recursive(schema)
        assert result == expected

    def test_non_dict_field_schema(self):
        """测试字段 schema 不是字典的情况"""
        schema = {
            "type": "object",
            "properties": {
                "valid_field": {"type": "string", "uiSchema": {"ui:widget": "text"}},
                "invalid_field": "not a dict",  # 不是字典
            },
        }
        expected = {
            "valid_field": {"ui:widget": "text"}
            # invalid_field 不应出现
        }
        result = extract_ui_schema_recursive(schema)
        assert result == expected

    def test_non_dict_items_schema(self):
        """测试数组 items 不是字典的情况"""
        schema = {
            "type": "array",
            "items": "not a dict",  # 不是字典
        }
        result = extract_ui_schema_recursive(schema)
        assert result == {}

    def test_array_without_items(self):
        """测试没有 items 的数组"""
        schema = {"type": "array", "uiSchema": {"ui:options": {"addable": True}}}
        expected = {"ui:options": {"addable": True}}
        result = extract_ui_schema_recursive(schema)
        assert result == expected

    def test_object_without_properties(self):
        """测试没有 properties 的对象"""
        schema = {"type": "object", "uiSchema": {"ui:title": "Empty Object"}}
        expected = {"ui:title": "Empty Object"}
        result = extract_ui_schema_recursive(schema)
        assert result == expected

    def test_neither_object_nor_array(self):
        """测试既不是对象也不是数组的类型"""
        schema = {"type": "string", "uiSchema": {"ui:widget": "password"}}
        expected = {"ui:widget": "password"}
        result = extract_ui_schema_recursive(schema)
        assert result == expected

    def test_empty_ui_schema_not_added(self):
        """测试空的 UI schema 不会被添加"""
        schema = {
            "type": "object",
            "properties": {
                "field_with_empty_ui": {
                    "type": "string"
                    # 没有 uiSchema，递归调用返回空字典
                },
                "field_with_ui": {"type": "string", "uiSchema": {"ui:widget": "text"}},
            },
        }
        expected = {
            "field_with_ui": {"ui:widget": "text"}
            # field_with_empty_ui 不应出现
        }
        result = extract_ui_schema_recursive(schema)
        assert result == expected
