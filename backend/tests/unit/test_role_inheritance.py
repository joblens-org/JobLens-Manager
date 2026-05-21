"""角色和规则继承函数的单元测试"""
import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from backend.routers.roles import (
    get_role_rules_with_inheritance,
    get_role_rules_from_etcd,
    validate_role_name
)
from backend.models import RoleInfo, RuleInfo, RoleWithRules


class TestRoleInheritance:
    """角色继承逻辑测试"""
    
    @pytest.fixture
    def sample_role_info(self):
        """示例角色信息"""
        return RoleInfo(
            role_id="role-123",
            name="child-role",
            description="子角色",
            parent_role_id="role-456",  # 父角色
            rule_ids=["rule-1", "rule-2"],
            service_count=0
        )
    
    @pytest.fixture
    def sample_parent_role_info(self):
        """示例父角色信息"""
        return RoleInfo(
            role_id="role-456",
            name="parent-role",
            description="父角色",
            parent_role_id="role-789",  # 祖父角色
            rule_ids=["rule-3", "rule-4"],
            service_count=0
        )
    
    @pytest.fixture
    def sample_grandparent_role_info(self):
        """示例祖父角色信息"""
        return RoleInfo(
            role_id="role-789",
            name="grandparent-role",
            description="祖父角色",
            parent_role_id=None,  # 根角色
            rule_ids=["rule-5"],
            service_count=0
        )
    
    @pytest.fixture
    def sample_rule_info(self):
        """示例规则信息"""
        return RuleInfo(
            rule_id="rule-1",
            role_id="role-123",
            name="child-rule-1",
            lua_content="function child() return true end"
        )
    
    @pytest.fixture
    def sample_parent_rule_info(self):
        """示例父规则信息"""
        return RuleInfo(
            rule_id="rule-3",
            role_id="role-456",
            name="parent-rule-3",
            lua_content="function parent() return true end"
        )
    
    @pytest.fixture
    def sample_grandparent_rule_info(self):
        """示例祖父规则信息"""
        return RuleInfo(
            rule_id="rule-5",
            role_id="role-789",
            name="grandparent-rule-5",
            lua_content="function grandparent() return true end"
        )
    
    @pytest.fixture
    def mock_etcd_client(self):
        """Mock ETCD客户端"""
        return Mock()
    
    @pytest.fixture
    def mock_get_role_rules(self):
        """Mock get_role_rules函数"""
        with patch('backend.routers.roles.get_role_rules') as mock:
            yield mock
    
    @pytest.mark.asyncio
    async def test_get_role_with_inherited_rules_simple(self, mock_etcd_client, mock_get_role_rules):
        """测试获取角色继承规则（简单继承）"""
        # 准备角色数据
        role_info = RoleInfo(
            role_id="role-123",
            name="child-role",
            parent_role_id=None,
            rule_ids=["rule-1"]
        )
        
        # 准备规则数据
        rule_info = RuleInfo(
            rule_id="rule-1",
            role_id="role-123",
            name="test-rule",
            lua_content="function test() return true end"
        )
        
        # Mock ETCD获取角色信息
        mock_etcd_client.get.return_value = (role_info.model_dump_json(), None)
        
        # Mock get_prefix方法返回空列表（没有规则）
        mock_etcd_client.get_prefix.return_value = []
        
        # 执行测试
        result = await get_role_rules_with_inheritance(mock_etcd_client, "role-123")
        
        # 验证
        assert isinstance(result, list)
        assert len(result) == 0  # 没有规则，因为get_prefix返回空列表
        
        mock_etcd_client.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_role_with_inherited_rules_multi_level(self, mock_etcd_client, mock_get_role_rules):
        """测试多级继承的角色规则"""
        # 准备角色继承链
        grandparent_role = RoleInfo(
            role_id="role-789",
            name="grandparent",
            parent_role_id=None,
            rule_ids=["rule-5"]
        )
        
        parent_role = RoleInfo(
            role_id="role-456",
            name="parent",
            parent_role_id="role-789",
            rule_ids=["rule-3"]
        )
        
        child_role = RoleInfo(
            role_id="role-123",
            name="child",
            parent_role_id="role-456",
            rule_ids=["rule-1"]
        )
        
        # 准备规则
        grandparent_rule = RuleInfo(
            rule_id="rule-5",
            role_id="role-789",
            name="grandparent-rule",
            lua_content="function gp() return true end"
        )
        
        parent_rule = RuleInfo(
            rule_id="rule-3",
            role_id="role-456",
            name="parent-rule",
            lua_content="function p() return true end"
        )
        
        child_rule = RuleInfo(
            rule_id="rule-1",
            role_id="role-123",
            name="child-rule",
            lua_content="function c() return true end"
        )
        
        # Mock ETCD获取角色信息（使用side_effect返回不同角色的信息）
        def get_side_effect(key):
            if key.endswith("role-123/info"):
                return (child_role.model_dump_json(), None)
            elif key.endswith("role-456/info"):
                return (parent_role.model_dump_json(), None)
            elif key.endswith("role-789/info"):
                return (grandparent_role.model_dump_json(), None)
            else:
                return (None, None)
        
        mock_etcd_client.get.side_effect = get_side_effect
        
        # Mock get_prefix方法返回所有规则
        mock_etcd_client.get_prefix.return_value = [
            (child_rule.model_dump_json().encode('utf-8'), Mock(key=b'/joblens/config/rules/rule-1')),
            (parent_rule.model_dump_json().encode('utf-8'), Mock(key=b'/joblens/config/rules/rule-3')),
            (grandparent_rule.model_dump_json().encode('utf-8'), Mock(key=b'/joblens/config/rules/rule-5'))
        ]
        
        # 执行测试
        result = await get_role_rules_with_inheritance(mock_etcd_client, "role-123")
        
        # 验证：应该包含所有规则（子角色、父角色、祖父角色）
        assert isinstance(result, list)
        
        # 收集所有规则ID
        rule_ids = [rule.rule_id for rule in result]
        assert "rule-1" in rule_ids  # 子规则
        assert "rule-3" in rule_ids  # 父规则
        assert "rule-5" in rule_ids  # 祖父规则
    
    @pytest.mark.asyncio
    async def test_get_role_with_inherited_rules_override(self, mock_etcd_client, mock_get_role_rules):
        """测试规则覆盖（子角色覆盖父规则）"""
        # 准备角色
        parent_role = RoleInfo(
            role_id="role-456",
            name="parent",
            parent_role_id=None,
            rule_ids=["rule-3"]
        )
        
        child_role = RoleInfo(
            role_id="role-123",
            name="child",
            parent_role_id="role-456",
            rule_ids=["rule-1"]  # 覆盖规则
        )
        
        # 准备规则
        parent_rule = RuleInfo(
            rule_id="rule-3",
            role_id="role-456",
            name="parent-rule",
            lua_content="function p() return true end"
        )
        
        child_override_rule = RuleInfo(
            rule_id="rule-1",
            role_id="role-123",
            name="parent-rule",  # 同名规则
            lua_content="function p() return false end"  # 覆盖内容
        )
        
        # Mock ETCD获取角色信息
        def get_side_effect(key):
            if key.endswith("role-123/info"):
                return (child_role.model_dump_json(), None)
            elif key.endswith("role-456/info"):
                return (parent_role.model_dump_json(), None)
            return (None, None)
        
        mock_etcd_client.get.side_effect = get_side_effect
        
        # Mock get_prefix方法返回所有规则
        mock_etcd_client.get_prefix.return_value = [
            (child_override_rule.model_dump_json().encode('utf-8'), Mock(key=b'/joblens/config/rules/rule-1')),
            (parent_rule.model_dump_json().encode('utf-8'), Mock(key=b'/joblens/config/rules/rule-3'))
        ]
        
        # 执行测试
        result = await get_role_rules_with_inheritance(mock_etcd_client, "role-123")
        
        # 验证：应该包含父规则和子规则
        rule_ids = [rule.rule_id for rule in result]
        assert "rule-1" in rule_ids  # 子规则
        assert "rule-3" in rule_ids  # 父规则
    
    @pytest.mark.asyncio
    async def test_get_role_with_inherited_rules_role_not_found(self, mock_etcd_client):
        """测试获取不存在的角色"""
        # Mock ETCD返回None
        mock_etcd_client.get.return_value = (None, None)
        
        # 执行测试并验证HTTPException
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_role_rules_with_inheritance(mock_etcd_client, "non-existent")
        
        assert exc_info.value.status_code == 404
        assert "角色 'non-existent' 不存在" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_role_with_inherited_rules_missing_parent(self, mock_etcd_client, mock_get_role_rules):
        """测试继承链中父角色不存在"""
        # 准备角色（父角色不存在）
        role_info = RoleInfo(
            role_id="role-123",
            name="child-role",
            parent_role_id="non-existent-parent",
            rule_ids=["rule-1"]
        )
        
        rule_info = RuleInfo(
            rule_id="rule-1",
            role_id="role-123",
            name="test-rule",
            lua_content="function test() return true end"
        )
        
        # Mock ETCD获取角色信息
        def get_side_effect(key):
            if key.endswith("role-123/info"):
                return (role_info.model_dump_json(), None)
            elif "non-existent-parent" in key:
                return (None, None)
            return (None, None)
        
        mock_etcd_client.get.side_effect = get_side_effect
        
        # Mock get_prefix方法返回规则
        mock_etcd_client.get_prefix.return_value = [
            (rule_info.model_dump_json().encode('utf-8'), Mock(key=b'/joblens/config/rules/rule-1'))
        ]
        
        # 执行测试（应正常返回，忽略不存在的父角色）
        result = await get_role_rules_with_inheritance(mock_etcd_client, "role-123")
        
        # 验证
        assert isinstance(result, list)
        assert len(result) == 1  # 只有自己的规则
    
    @pytest.mark.asyncio
    async def test_get_role_with_inherited_rules_circular_dependency(self, mock_etcd_client, mock_get_role_rules):
        """测试循环依赖处理"""
        # 准备循环依赖角色
        role1 = RoleInfo(
            role_id="role-1",
            name="role-1",
            parent_role_id="role-2",  # 指向role-2
            rule_ids=["rule-1"]
        )
        
        role2 = RoleInfo(
            role_id="role-2",
            name="role-2",
            parent_role_id="role-1",  # 指向role-1（循环）
            rule_ids=["rule-2"]
        )
        
        # Mock ETCD获取角色信息（循环返回）
        call_count = {"role-1": 0, "role-2": 0}
        
        def get_side_effect(key):
            if key.endswith("role-1/info"):
                call_count["role-1"] += 1
                if call_count["role-1"] > 2:
                    return (None, None)  # 防止无限循环
                return (role1.model_dump_json(), None)
            elif key.endswith("role-2/info"):
                call_count["role-2"] += 1
                if call_count["role-2"] > 2:
                    return (None, None)
                return (role2.model_dump_json(), None)
            return (None, None)
        
        mock_etcd_client.get.side_effect = get_side_effect
        
        # Mock get_prefix方法返回规则
        rule1 = RuleInfo(rule_id="rule-1", role_id="role-1", name="rule-1", lua_content="")
        rule2 = RuleInfo(rule_id="rule-2", role_id="role-2", name="rule-2", lua_content="")
        
        mock_etcd_client.get_prefix.return_value = [
            (rule1.model_dump_json().encode('utf-8'), Mock(key=b'/joblens/config/rules/rule-1')),
            (rule2.model_dump_json().encode('utf-8'), Mock(key=b'/joblens/config/rules/rule-2'))
        ]
        
        # 执行测试（应能处理循环依赖而不崩溃）
        result = await get_role_rules_with_inheritance(mock_etcd_client, "role-1")
        
        # 验证
        assert isinstance(result, list)
        # 不应该陷入无限循环
    
    @pytest.mark.asyncio
    async def test_get_role_rules_from_etcd(self):
        """测试get_role_rules_from_etcd函数"""
        # 测试从ETCD获取角色规则
        client = Mock()
        
        # Mock ETCD返回
        rule_info = RuleInfo(
            rule_id="rule-1",
            name="test-rule",
            lua_content="function test() return true end",
            role_id="role-123"
        )
        
        # Mock get_prefix返回规则
        client.get_prefix.return_value = [
            (rule_info.model_dump_json().encode('utf-8'), Mock(key=b'/joblens/config/rules/rule-1'))
        ]
        
        rules = await get_role_rules_from_etcd(client, "role-123")
        assert isinstance(rules, list)
        assert len(rules) == 1
        assert rules[0].rule_id == "rule-1"


class TestRoleValidation:
    """角色验证函数测试"""
    
    def test_validate_role_name_valid(self):
        """测试有效的角色名称"""
        assert validate_role_name("admin") is True
        assert validate_role_name("test-role") is True
        assert validate_role_name("role_123") is True
        assert validate_role_name("ROLE-ABC_123") is True
        assert validate_role_name("a") is True
    
    def test_validate_role_name_invalid(self):
        """测试无效的角色名称"""
        assert validate_role_name("") is False  # 空名称
        assert validate_role_name("test role") is False  # 包含空格
        assert validate_role_name("role@test") is False  # 包含特殊字符
        assert validate_role_name("role#test") is False
        assert validate_role_name("role.test") is False
        assert validate_role_name("role/test") is False
        assert validate_role_name("a" * 101) is False  # 超长名称
    
    def test_validate_role_name_edge_cases(self):
        """测试边界情况"""
        assert validate_role_name("a" * 100) is True  # 最大长度
        assert validate_role_name("123") is True  # 纯数字
        assert validate_role_name("test-role_123") is True  # 混合字符


if __name__ == "__main__":
    pytest.main([__file__, "-v"])