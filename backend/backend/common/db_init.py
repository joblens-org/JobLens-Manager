from backend.common.etcd_client import get_etcd_client
from backend.config import settings
from backend.routers.modes import get_default_mode, create_mode_sync
from backend.routers.roles import get_default_role_id, set_default_role_id, create_role_sync
from backend.common.logger import logger


def initialize_etcd():
    """初始化 ETCD 连接并设置默认模式和角色"""
    client = get_etcd_client()
    try:
        # 尝试获取一个键来验证连接
        client.status()
        logger.info("成功连接到 ETCD")
    except Exception as e:
        logger.error(f"无法连接到 ETCD: {str(e)}")
        raise ConnectionError(f"无法连接到 ETCD: {str(e)}")
    
    # 初始化默认模式
    default_mode = get_default_mode(client)
    if default_mode:
        logger.info(f"默认模式已存在: {default_mode}")
    else:
        logger.info("默认模式不存在，正在创建...")
        try:
            # 使用 create_mode_sync 创建默认模式
            mode_info = create_mode_sync(
                client=client,
                name=settings.default_mode_name,
                description="默认模式",
                default=True
            )
            logger.info(f"默认模式已创建: {mode_info.name}")
        except Exception as e:
            logger.error(f"创建默认模式失败: {str(e)}")
            raise
    
    # 初始化默认角色
    default_role_id = get_default_role_id(client)
    if default_role_id:
        logger.info(f"默认角色已存在: {default_role_id}")
    else:
        logger.info("默认角色不存在，正在创建...")
        try:
            # 使用 create_role_sync 创建默认角色
            role_info = create_role_sync(
                client=client,
                name=settings.default_role_name,
                description="默认角色",
                rule_ids=[]
            )
            # 设置为默认角色
            set_default_role_id(client=client, role_id=role_info.role_id)
            logger.info(f"默认角色已创建: {role_info.name} ({role_info.role_id})")
        except Exception as e:
            logger.error(f"创建默认角色失败: {str(e)}")
            raise
