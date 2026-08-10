import lupa
from typing import Dict, Any, Optional
from fastapi import HTTPException
from ..common.logger import logger


class LuaValidator:
    """Lua规则验证服务"""
    
    def __init__(self):
        self.lua = lupa.LuaRuntime()
        logger.debug("LuaValidator初始化完成")
        
    def validate_lua_syntax(self, lua_content: str) -> bool:
        """验证Lua语法是否正确"""
        try:
            self.lua.execute(lua_content)
            return True
        except lupa.LuaError as e:
            logger.warning(f"Lua语法验证失败 content_length={len(lua_content)} error={str(e)}")
            raise HTTPException(
                status_code=400, 
                detail=f"Lua语法错误: {str(e)}"
            )
    
    def validate_rule_structure(self, lua_content: str) -> Dict[str, Any]:
        """验证规则结构是否符合要求"""
        try:
            # 执行Lua代码
            self.lua.execute(lua_content)
            
            # 检查rule变量是否存在
            rule = self.lua.eval("rule")
            if rule is None:
                logger.warning(f"规则结构验证失败 content_length={len(lua_content)} reason=缺少rule变量")
                raise HTTPException(
                    status_code=400,
                    detail="规则必须包含'rule'变量"
                )
            
            # 验证必需字段
            required_fields = ['name', 'description', 'priority', 'condition']
            for field in required_fields:
                if field not in rule:
                    logger.warning(f"规则结构验证失败 content_length={len(lua_content)} field={field} reason=缺少必需字段")
                    raise HTTPException(
                        status_code=400,
                        detail=f"规则必须包含'{field}'字段"
                    )
            
            # 验证字段类型
            if not isinstance(rule['name'], str):
                logger.warning(f"规则字段类型错误 content_length={len(lua_content)} field=name expected_type=str")
                raise HTTPException(
                    status_code=400,
                    detail="'name'字段必须是字符串"
                )
            
            if not isinstance(rule['description'], str):
                logger.warning(f"规则字段类型错误 content_length={len(lua_content)} field=description expected_type=str")
                raise HTTPException(
                    status_code=400,
                    detail="'description'字段必须是字符串"
                )
            
            if not isinstance(rule['priority'], (int, float)):
                logger.warning(f"规则字段类型错误 content_length={len(lua_content)} field=priority expected_type=number")
                raise HTTPException(
                    status_code=400,
                    detail="'priority'字段必须是数字"
                )
            
            if not callable(rule['condition']):
                logger.warning(f"规则字段类型错误 content_length={len(lua_content)} field=condition expected_type=function")
                raise HTTPException(
                    status_code=400,
                    detail="'condition'字段必须是函数"
                )
            
            return dict(rule)
            
        except lupa.LuaError as e:
            logger.warning(f"Lua执行错误 content_length={len(lua_content)} error={str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Lua执行错误: {str(e)}"
            )
    
    def validate_rule(self, lua_content: str) -> Dict[str, Any]:
        """完整验证规则"""
        # 1. 验证语法
        self.validate_lua_syntax(lua_content)
        
        # 2. 验证结构
        rule_structure = self.validate_rule_structure(lua_content)
        
        logger.info(f"Lua规则验证成功 content_length={len(lua_content)}")

        return rule_structure


# 全局验证器实例
_lua_validator_instance = None


def get_lua_validator() -> LuaValidator:
    """获取Lua验证器实例"""
    global _lua_validator_instance
    if _lua_validator_instance is None:
        _lua_validator_instance = LuaValidator()
    return _lua_validator_instance


def set_lua_validator(validator: LuaValidator) -> None:
    """设置Lua验证器实例（用于测试）"""
    global _lua_validator_instance
    _lua_validator_instance = validator


def reset_lua_validator() -> None:
    """重置Lua验证器实例"""
    global _lua_validator_instance
    _lua_validator_instance = None
