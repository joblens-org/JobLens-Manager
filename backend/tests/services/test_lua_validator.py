"""LuaValidator服务层测试"""
import pytest
from unittest.mock import patch, Mock
from fastapi import HTTPException


class TestLuaValidator:
    """LuaValidator核心功能测试"""

    @pytest.fixture
    def validator(self):
        from backend.services.lua_validator import LuaValidator
        return LuaValidator()

    # ─── validate_lua_syntax ───

    def test_validate_lua_syntax_valid(self, validator):
        result = validator.validate_lua_syntax("local x = 1")
        assert result is True

    def test_validate_lua_syntax_complex(self, validator):
        code = """
        function test(ctx)
            return ctx.value > 10
        end
        """
        assert validator.validate_lua_syntax(code) is True

    def test_validate_lua_syntax_empty(self, validator):
        assert validator.validate_lua_syntax("") is True

    def test_validate_lua_syntax_invalid_syntax(self, validator):
        with pytest.raises(HTTPException) as exc:
            validator.validate_lua_syntax("local x = ")
        assert exc.value.status_code == 400
        assert "语法错误" in exc.value.detail

    def test_validate_lua_syntax_invalid_expression(self, validator):
        with pytest.raises(HTTPException) as exc:
            validator.validate_lua_syntax("if true then")
        assert exc.value.status_code == 400

    # ─── validate_rule_structure ───

    VALID_RULE = """
    rule = {
        name = "test_rule",
        description = "A test rule description",
        priority = 1,
        condition = function(ctx)
            return ctx.value > 10
        end
    }
    """

    def test_validate_rule_structure_valid(self, validator):
        result = validator.validate_rule_structure(self.VALID_RULE)
        assert result["name"] == "test_rule"
        assert result["description"] == "A test rule description"
        assert result["priority"] == 1
        assert callable(result["condition"])

    def test_validate_rule_structure_no_rule_variable(self, validator):
        with pytest.raises(HTTPException) as exc:
            validator.validate_rule_structure("local x = 1")
        assert exc.value.status_code == 400
        assert "rule" in exc.value.detail

    def test_validate_rule_structure_rule_is_nil(self, validator):
        with pytest.raises(HTTPException) as exc:
            validator.validate_rule_structure("rule = nil")
        assert exc.value.status_code == 400
        assert "rule" in exc.value.detail

    def test_validate_rule_structure_missing_name(self, validator):
        code = """
        rule = {
            description = "desc",
            priority = 1,
            condition = function() end
        }
        """
        with pytest.raises(HTTPException) as exc:
            validator.validate_rule_structure(code)
        assert exc.value.status_code == 400
        assert "name" in exc.value.detail

    def test_validate_rule_structure_missing_description(self, validator):
        code = """
        rule = {
            name = "test",
            priority = 1,
            condition = function() end
        }
        """
        with pytest.raises(HTTPException) as exc:
            validator.validate_rule_structure(code)
        assert exc.value.status_code == 400
        assert "description" in exc.value.detail

    def test_validate_rule_structure_missing_priority(self, validator):
        code = """
        rule = {
            name = "test",
            description = "desc",
            condition = function() end
        }
        """
        with pytest.raises(HTTPException) as exc:
            validator.validate_rule_structure(code)
        assert exc.value.status_code == 400
        assert "priority" in exc.value.detail

    def test_validate_rule_structure_missing_condition(self, validator):
        code = """
        rule = {
            name = "test",
            description = "desc",
            priority = 1
        }
        """
        with pytest.raises(HTTPException) as exc:
            validator.validate_rule_structure(code)
        assert exc.value.status_code == 400
        assert "condition" in exc.value.detail

    def test_validate_rule_structure_name_not_string(self, validator):
        code = """
        rule = {
            name = 123,
            description = "desc",
            priority = 1,
            condition = function() end
        }
        """
        with pytest.raises(HTTPException) as exc:
            validator.validate_rule_structure(code)
        assert exc.value.status_code == 400
        assert "name" in exc.value.detail
        assert "字符串" in exc.value.detail

    def test_validate_rule_structure_priority_not_number(self, validator):
        code = """
        rule = {
            name = "test",
            description = "desc",
            priority = "high",
            condition = function() end
        }
        """
        with pytest.raises(HTTPException) as exc:
            validator.validate_rule_structure(code)
        assert exc.value.status_code == 400
        assert "priority" in exc.value.detail

    def test_validate_rule_structure_condition_not_function(self, validator):
        code = """
        rule = {
            name = "test",
            description = "desc",
            priority = 1,
            condition = "not_a_function"
        }
        """
        with pytest.raises(HTTPException) as exc:
            validator.validate_rule_structure(code)
        assert exc.value.status_code == 400
        assert "condition" in exc.value.detail

    def test_validate_rule_structure_lua_error(self, validator):
        with pytest.raises(HTTPException) as exc:
            validator.validate_rule_structure("invalid lua {{ content")
        assert exc.value.status_code == 400
        assert "Lua" in exc.value.detail

    # ─── validate_rule（完整验证） ───

    def test_validate_rule_valid(self, validator):
        result = validator.validate_rule(self.VALID_RULE)
        assert result["name"] == "test_rule"
        assert result["priority"] == 1

    def test_validate_rule_syntax_error(self, validator):
        with pytest.raises(HTTPException) as exc:
            validator.validate_rule("broken syntax {{")
        assert exc.value.status_code == 400

    def test_validate_rule_structure_error(self, validator):
        code = """
        rule = {
            name = "test"
        }
        """
        with pytest.raises(HTTPException) as exc:
            validator.validate_rule(code)
        assert exc.value.status_code == 400
        assert "description" in exc.value.detail


class TestLuaValidatorSingleton:
    """全局验证器实例测试"""

    def teardown_method(self):
        from backend.services.lua_validator import reset_lua_validator
        reset_lua_validator()

    def test_get_lua_validator_default(self):
        from backend.services.lua_validator import get_lua_validator, reset_lua_validator
        reset_lua_validator()
        validator = get_lua_validator()
        assert validator is not None
        assert hasattr(validator, 'validate_lua_syntax')

    def test_get_lua_validator_singleton(self):
        from backend.services.lua_validator import get_lua_validator, reset_lua_validator
        reset_lua_validator()
        v1 = get_lua_validator()
        v2 = get_lua_validator()
        assert v1 is v2

    def test_set_lua_validator(self):
        from backend.services.lua_validator import get_lua_validator, set_lua_validator, reset_lua_validator
        from unittest.mock import Mock
        reset_lua_validator()
        mock = Mock()
        set_lua_validator(mock)
        assert get_lua_validator() is mock

    def test_reset_lua_validator(self):
        from backend.services.lua_validator import get_lua_validator, set_lua_validator, reset_lua_validator
        from unittest.mock import Mock
        reset_lua_validator()
        mock = Mock()
        set_lua_validator(mock)
        reset_lua_validator()
        v = get_lua_validator()
        assert v is not mock


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
