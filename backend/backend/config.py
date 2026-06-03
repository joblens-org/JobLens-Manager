from pydantic import Field, validator, field_validator
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """
    应用配置类
    优先级：环境变量 > .env文件 > 默认值
    """
    
    # ==================== 认证配置 ====================
    admin_password: str = Field(
        default="admin",
        env="ADMIN_PASSWORD",
        description="管理员登录密码"
    )
    auth_whitelist_ips: str = Field(
        default="",
        env="AUTH_WHITELIST_IPS",
        description="白名单 IP，逗号分隔，支持 CIDR（如 127.0.0.1,10.0.0.0/8），白名单 IP 调用接口免认证"
    )

    # ==================== 通用配置 ====================
    registry_url: str = Field(
        default="http://localhost:8080",
        env="REGISTRY_URL",
        description="注册中心URL"
    )
    collector_timeout: float = Field(
        default=5.0,
        env="COLLECTOR_TIMEOUT",
        description="采集器超时时间(秒)"
    )
    cache_ttl: int = Field(
        default=30,
        env="CACHE_TTL",
        ge=0,  # 必须大于等于0
        description="缓存TTL(秒)"
    )
    
    # ==================== 数据库初始化配置 ====================
    default_mode_name: str = Field(
        default="default",
        env="DEFAULT_MODE_NAME",
        description="默认模式名称"
    )
    
    default_role_name: str = Field(
        default="default",
        env="DEFAULT_ROLE_NAME",
        description="默认角色名称"
    )

    # ==================== ETCD 连接配置 ====================
    etcd_host: str = Field(
        default="localhost",
        env="ETCD_HOST",
        description="ETCD主机地址"
    )
    etcd_port: int = Field(
        default=2379,
        env="ETCD_PORT",
        ge=1,
        le=65535,
        description="ETCD端口"
    )
    etcd_timeout: int = Field(
        default=10,
        env="ETCD_TIMEOUT",
        gt=0,  # 必须大于0
        description="ETCD连接超时(秒)"
    )

    # ==================== 配置节点路径 ====================
    etcd_config_prefix: str = Field(
        default="/joblens/config/",
        env="ETCD_CONFIG_PREFIX",
        description="ETCD配置前缀路径"
    )
    etcd_services_prefix: str = Field(
        default="/joblens_registry/services/",
        env="ETCD_REGISTRY_PREFIX",
        description="ETCD注册中心前缀路径"
    )
    etcd_clusters_instance_prefix: str = Field(
        default="/joblens_registry/clusters/instance/",
        env="ETCD_CLUSTERS_INSTANCE_PREFIX",
        description="ETCD集群实例路径前缀（注册中心自动发现）"
    )

    # 可选：调试模式（示例新增配置）
    debug: bool = Field(
        default=False,
        env="DEBUG",
        description="调试模式开关"
    )
    log_path: str = Field(
        default="./joblens_web_manager.log",
        env="LOG_PATH",
        description="日志文件路径"
    )
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
        description="日志级别"
    )

    # ==================== 验证器 ====================
    @field_validator('registry_url')
    def validate_and_clean_url(cls, v):
        """验证URL格式并清理首尾空格，无协议时自动补 http://"""
        v = v.strip()
        if not v.startswith(('http://', 'https://')):
            v = f"http://{v}"
        return v


    # ==================== 配置类属性 ====================
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = False  # 环境变量名大小写不敏感（Linux默认大写）
        # env_prefix = "APP_"    # 如需前缀，取消注释：所有环境变量需以 APP_ 开头

    def __repr__(self):
        """自定义输出，隐藏敏感信息"""
        return f"<Settings etcd={self.etcd_host}:{self.etcd_port} registry={self.registry_url}>"


# 单例模式实例化
settings = Settings()

# 便捷函数：重新加载配置（用于运行时刷新）
def reload_settings() -> Settings:
    """重新从环境变量加载配置"""
    global settings
    settings = Settings()
    return settings


# ==================== 使用示例 ====================
if __name__ == "__main__":
    # 查看当前配置
    print(f"Registry URL: {settings.registry_url}")
    print(f"ETCD Endpoint: {settings.etcd_host}:{settings.etcd_port}")
    print(f"Debug Mode: {settings.debug}")
    
    # 检查配置来源（调试用）
    print("\n配置详情:", settings)