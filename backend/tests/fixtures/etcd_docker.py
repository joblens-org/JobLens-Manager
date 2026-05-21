import docker
import pytest
import time
import etcd3
import logging

logger = logging.getLogger(__name__)


class EtcdDockerManager:
    """管理ETCD Docker容器的生命周期"""
    
    def __init__(self):
        self.client = None
        self.container = None
        self.host = "localhost"
        self.port = 12379  # 测试端口，避免与生产环境冲突
        
    def start(self):
        """启动ETCD容器"""
        try:
            self.client = docker.from_env()
            logger.info(f"启动ETCD容器，端口: {self.port}")
            
            self.container = self.client.containers.run(
                "bitnami/etcd:latest",
                environment={
                    "ALLOW_NONE_AUTHENTICATION": "yes",
                    "ETCD_ADVERTISE_CLIENT_URLS": f"http://0.0.0.0:{self.port}",
                    "ETCD_LISTEN_CLIENT_URLS": f"http://0.0.0.0:{self.port}"
                },
                ports={f'{self.port}/tcp': self.port},
                detach=True,
                remove=True,
                stdout=False,
                stderr=False
            )
            
            # 等待容器就绪
            self._wait_for_ready()
            logger.info(f"ETCD容器已启动，容器ID: {self.container.id[:12]}")
            
            return self.host, self.port
        except Exception as e:
            logger.error(f"启动ETCD容器失败: {e}")
            self.stop()
            raise
    
    def _wait_for_ready(self, max_retries=30, wait_interval=1):
        """等待ETCD服务就绪"""
        for i in range(max_retries):
            try:
                client = etcd3.client(host=self.host, port=self.port, timeout=2)
                client.status()
                logger.info(f"ETCD服务在第{i+1}次尝试后已就绪")
                return True
            except Exception:
                time.sleep(wait_interval)
        raise TimeoutError(f"ETCD服务在{max_retries * wait_interval}秒后仍未就绪")
    
    def stop(self):
        """停止ETCD容器"""
        if self.container:
            try:
                logger.info(f"停止ETCD容器: {self.container.id[:12]}")
                self.container.stop(timeout=5)
                self.container = None
            except Exception as e:
                logger.warning(f"停止ETCD容器时出错: {e}")
        
        if self.client:
            self.client.close()
            self.client = None
    
    def get_client(self):
        """获取ETCD客户端连接"""
        return etcd3.client(host=self.host, port=self.port, timeout=10)
    
    def cleanup_data(self):
        """清理测试数据"""
        try:
            client = self.get_client()
            client.delete_prefix("/test/")
            client.delete_prefix("/software/config/")  # 清理配置路径
            logger.info("已清理ETCD测试数据")
        except Exception as e:
            logger.warning(f"清理ETCD数据时出错: {e}")


def etcd_docker_fixture():
    """生成ETCD Docker容器的fixture函数"""
    manager = None
    
    def _create_fixture():
        nonlocal manager
        manager = EtcdDockerManager()
        manager.start()
        return manager
    
    def _finalize():
        if manager:
            manager.cleanup_data()
            manager.stop()
    
    # 返回一个可调用对象，pytest fixture将使用它
    return _create_fixture, _finalize


# 导出fixture创建函数
__all__ = ['EtcdDockerManager', 'etcd_docker_fixture']