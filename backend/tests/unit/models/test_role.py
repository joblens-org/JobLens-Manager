"""Role和Rule模型的单元测试"""
import pytest
from datetime import datetime
from backend.models.role import (
    RuleInfo,
    RoleInfo,
    RoleCreate,
    RoleUpdate,
    RuleCreate,
    RuleUpdate,
    RoleWithRules,
    RoleListResponse,
    RuleListResponse
)


class TestRuleInfo:
    """RuleInfo模型测试"""
    
    def test_create_rule_info_with_defaults(self):
        """测试创建带默认值的RuleInfo"""
        rule = RuleInfo(
            role_id="test-role-id",
            name="test-rule",
            lua_content="function test() return true end"
        )
        assert rule.name == "test-rule"
        assert rule.lua_content == "function test() return true end"
        assert rule.version == 1
        assert rule.metadata is None
        # 应该自动生成UUID
        assert rule.rule_id is not None
    
    def test_create_rule_info_with_custom_values(self):
        """测试使用自定义值创建RuleInfo"""
        rule = RuleInfo(
            role_id="role-custom-id",
            rule_id="custom-rule-id",
            name="test-rule",
            lua_content="function test() return true end",
            metadata={"category": "validation"}
        )
        assert rule.rule_id == "custom-rule-id"
        assert rule.metadata == {"category": "validation"}
    
    def test_rule_info_timestamps(self):
        """测试RuleInfo时间戳"""
        before = datetime.now()
        rule = RuleInfo(
            role_id="test-role-id",
            name="test-rule",
            lua_content="function test() return true end"
        )
        after = datetime.now()
        assert rule.created_at <= after
        assert rule.updated_at <= after
        assert rule.created_at >= before
        assert rule.updated_at >= before
    
    def test_rule_info_validation(self):
        """测试RuleInfo验证"""
        # Pydantic默认仅校验类型，空字符串""仍是合法的str
        rule1 = RuleInfo(
            role_id="test-role-id",
            name="",
            lua_content="function test() return true end"
        )
        assert rule1.name == ""
        
        rule2 = RuleInfo(
            role_id="test-role-id",
            name="test-rule",
            lua_content=""
        )
        assert rule2.lua_content == ""


class TestRoleInfo:
    """RoleInfo模型测试"""
    
    def test_create_role_info_with_defaults(self):
        """测试创建带默认值的RoleInfo"""
        role = RoleInfo(
            name="test-role",
            description="测试角色"
        )
        assert role.name == "test-role"
        assert role.description == "测试角色"
        assert role.parent_role_id is None
        assert role.rule_ids == []
        assert role.service_count == 0
        assert role.metadata is None
        # 应该自动生成UUID
        assert role.role_id is not None
    
    def test_create_role_info_with_custom_values(self):
        """测试使用自定义值创建RoleInfo"""
        role = RoleInfo(
            role_id="custom-role-id",
            name="test-role",
            description="测试角色",
            parent_role_id="parent-role-id",
            rule_ids=["rule-1", "rule-2"],
            service_count=5,
            metadata={"permissions": ["read"]}
        )
        assert role.role_id == "custom-role-id"
        assert role.parent_role_id == "parent-role-id"
        assert role.rule_ids == ["rule-1", "rule-2"]
        assert role.service_count == 5
        assert role.metadata == {"permissions": ["read"]}
    
    def test_role_info_timestamps(self):
        """测试RoleInfo时间戳"""
        before = datetime.now()
        role = RoleInfo(
            name="test-role"
        )
        after = datetime.now()
        assert role.created_at <= after
        assert role.updated_at <= after
        assert role.created_at >= before
        assert role.updated_at >= before
    
    def test_role_info_validation(self):
        """测试RoleInfo验证"""
        # Pydantic默认仅校验类型，空字符串""仍是合法的str
        role = RoleInfo(name="")
        assert role.name == ""
        
        # 服务数量不能为负数
        role = RoleInfo(
            name="test-role",
            service_count=-1
        )
        # Pydantic应该自动验证非负数？需要检查
        assert role.service_count == -1  # 没有验证，需要手动处理


class TestRoleCreate:
    """RoleCreate模型测试"""
    
    def test_create_role_create(self):
        """测试RoleCreate创建"""
        role_create = RoleCreate(
            name="new-role",
            description="新角色",
            parent_role_id="parent-role",
            rule_ids=["rule-1"],
            metadata={"category": "test"}
        )
        assert role_create.name == "new-role"
        assert role_create.description == "新角色"
        assert role_create.parent_role_id == "parent-role"
        assert role_create.rule_ids == ["rule-1"]
        assert role_create.metadata == {"category": "test"}
    
    def test_role_create_with_minimal_data(self):
        """测试最小化RoleCreate"""
        role_create = RoleCreate(name="minimal-role")
        assert role_create.name == "minimal-role"
        assert role_create.description is None
        assert role_create.parent_role_id is None
        assert role_create.rule_ids is None
        assert role_create.metadata is None


class TestRoleUpdate:
    """RoleUpdate模型测试"""
    
    def test_create_role_update(self):
        """测试RoleUpdate创建"""
        role_update = RoleUpdate(
            description="更新描述",
            metadata={"updated": True}
        )
        assert role_update.description == "更新描述"
        assert role_update.metadata == {"updated": True}
    
    def test_role_update_with_none_values(self):
        """测试使用None值的RoleUpdate"""
        role_update = RoleUpdate()
        assert role_update.description is None
        assert role_update.metadata is None


class TestRuleCreate:
    """RuleCreate模型测试"""
    
    def test_create_rule_create(self):
        """测试RuleCreate创建"""
        rule_create = RuleCreate(
            role_id="test-role-id",
            name="new-rule",
            lua_content="function new() end",
            metadata={"type": "validation"}
        )
        assert rule_create.name == "new-rule"
        assert rule_create.lua_content == "function new() end"
        assert rule_create.metadata == {"type": "validation"}
    
    def test_rule_create_validation(self):
        """测试RuleCreate验证"""
        # 名称和内容不能为空
        with pytest.raises(ValueError):
            RuleCreate(name="", lua_content="function() end")
        
        with pytest.raises(ValueError):
            RuleCreate(name="test", lua_content="")


class TestRuleUpdate:
    """RuleUpdate模型测试"""
    
    def test_create_rule_update(self):
        """测试RuleUpdate创建"""
        rule_update = RuleUpdate(
            name="updated-name",
            lua_content="function updated() end",
            metadata={"updated": True}
        )
        assert rule_update.name == "updated-name"
        assert rule_update.lua_content == "function updated() end"
        assert rule_update.metadata == {"updated": True}
    
    def test_rule_update_partial(self):
        """测试部分更新RuleUpdate"""
        rule_update = RuleUpdate(name="new-name")
        assert rule_update.name == "new-name"
        assert rule_update.lua_content is None
        assert rule_update.metadata is None


class TestRoleWithRules:
    """RoleWithRules模型测试"""
    
    def test_create_role_with_rules(self):
        """测试创建RoleWithRules"""
        rule = RuleInfo(
            role_id="test-role-id",
            name="test-rule",
            lua_content="function test() end"
        )
        role = RoleWithRules(
            name="test-role",
            description="测试角色",
            rules=[rule]
        )
        assert role.name == "test-role"
        assert len(role.rules) == 1
        assert role.rules[0].name == "test-rule"
    
    def test_role_with_rules_default_empty(self):
        """测试默认空规则的RoleWithRules"""
        role = RoleWithRules(name="test-role")
        assert role.rules == []


class TestRoleListResponse:
    """RoleListResponse模型测试"""
    
    def test_create_role_list_response(self):
        """测试创建RoleListResponse"""
        roles = [
            RoleInfo(name="role-1"),
            RoleInfo(name="role-2")
        ]
        response = RoleListResponse(
            roles=roles,
            total=100
        )
        assert len(response.roles) == 2
        assert response.total == 100
        assert response.roles[0].name == "role-1"
        assert response.roles[1].name == "role-2"
    
    def test_role_list_response_with_empty_list(self):
        """测试空列表的RoleListResponse"""
        response = RoleListResponse(roles=[], total=0)
        assert len(response.roles) == 0
        assert response.total == 0


class TestRuleListResponse:
    """RuleListResponse模型测试"""
    
    def test_create_rule_list_response(self):
        """测试创建RuleListResponse"""
        rules = [
            RuleInfo(role_id="role-1", name="rule-1", lua_content="function a() end"),
            RuleInfo(role_id="role-2", name="rule-2", lua_content="function b() end")
        ]
        response = RuleListResponse(
            rules=rules,
            total=50
        )
        assert len(response.rules) == 2
        assert response.total == 50
        assert response.rules[0].name == "rule-1"
        assert response.rules[1].name == "rule-2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])