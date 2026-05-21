"""
ETCD 客户端管理模块
使用单例模式确保全局只有一个 ETCD 客户端实例
"""
import etcd3
from backend.config import settings
from backend.common.logger import logger


class EtcdClientManager:
    """ETCD 客户端管理器（单例模式）"""
    
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EtcdClientManager, cls).__new__(cls)
        return cls._instance
    
    def get_client(self):
        """获取 ETCD 客户端实例（懒加载）"""
        if self._client is None:
            try:
                self._client = etcd3.client(
                    host=settings.etcd_host,
                    port=settings.etcd_port,
                    timeout=settings.etcd_timeout
                )
                logger.info(f"ETCD 客户端已创建: {settings.etcd_host}:{settings.etcd_port}")
            except Exception as e:
                logger.error(f"ETCD 连接失败: {str(e)}")
                raise ConnectionError(f"无法连接到 ETCD: {str(e)}")
        
        return self._client
    
    def reset_client(self):
        """重置客户端（用于测试或重新连接）"""
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
        self._client = None
        logger.info("ETCD 客户端已重置")
    
    def close(self):
        """关闭客户端连接"""
        if self._client is not None:
            try:
                self._client.close()
                logger.info("ETCD 客户端已关闭")
            except Exception as e:
                logger.warning(f"关闭 ETCD 客户端时出错: {str(e)}")
        self._client = None


# 全局单例实例
_etcd_manager = EtcdClientManager()


def get_etcd_client():
    """
    获取 ETCD 客户端实例（全局单例）
    
    Returns:
        etcd3.Client: ETCD 客户端实例
        
    Raises:
        ConnectionError: 如果无法连接到 ETCD
    """
    return _etcd_manager.get_client()


def reset_etcd_client():
    """重置 ETCD 客户端（用于测试或重新连接）"""
    _etcd_manager.reset_client()


def close_etcd_client():
    """关闭 ETCD 客户端连接"""
    _etcd_manager.close()
