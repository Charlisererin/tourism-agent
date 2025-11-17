# -*- coding: utf-8 -*-
import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional


class MemoryStorage(ABC):
    """记忆存储抽象接口"""

    @abstractmethod
    def save_message(self, user_id: str, session_id: str, role: str, content: str,
                     metadata: Dict[str, Any] = None) -> bool:
        """保存消息到存储"""
        pass

    @abstractmethod
    def get_history(self, user_id: str, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取历史记录"""
        pass

    @abstractmethod
    def clear_history(self, user_id: str, session_id: str) -> bool:
        """清除历史记录"""
        pass

    @abstractmethod
    def initialize(self) -> bool:
        """初始化存储"""
        pass

    @abstractmethod
    def close(self) -> None:
        """关闭存储连接"""
        pass


@dataclass
class APIConfig:
    """API配置"""
    api_key: str = None
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    timeout: int = 60
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class ModelConfig:
    """模型配置"""
    default_model: str = "qwen-plus"
    default_temperature: float = 0.7
    default_max_tokens: int = 2000
    default_system_message: str = None
    available_models: List[str] = field(default_factory=lambda: [
        "qwen-plus", "qwen-max", "qwen-vl-plus", "qwen-vl-max"
    ])


@dataclass
class MemoryConfig:
    """记忆配置"""
    enabled: bool = True
    storage_type: str = "mongodb"  # mongodb, redis, file, custom
    max_history_length: int = 10
    ttl_hours: int = 24 * 7  # 7天
    # MongoDB配置
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_database: str = "qianwen_memory"
    mongo_collection: str = "conversations"
    # Redis配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = None
    # 文件存储配置
    file_storage_path: str = "./memory_data"
    # 自定义存储实例
    custom_storage: MemoryStorage = None


@dataclass
class QianwenConfig:
    """千问工具类主配置"""
    api: APIConfig = field(default_factory=APIConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)

    @classmethod
    def from_env(cls) -> 'QianwenConfig':
        """从环境变量创建配置"""
        config = cls()

        # API配置
        config.api.api_key = os.getenv('QIANWEN_API_KEY') or os.getenv('DASHSCOPE_API_KEY')
        config.api.base_url = os.getenv('QIANWEN_BASE_URL', config.api.base_url)
        config.api.timeout = int(os.getenv('QIANWEN_TIMEOUT', config.api.timeout))

        # 模型配置
        config.model.default_model = os.getenv('QIANWEN_DEFAULT_MODEL', config.model.default_model)
        config.model.default_temperature = float(
            os.getenv('QIANWEN_DEFAULT_TEMPERATURE', config.model.default_temperature))
        config.model.default_max_tokens = int(os.getenv('QIANWEN_DEFAULT_MAX_TOKENS', config.model.default_max_tokens))
        config.model.default_system_message = os.getenv('QIANWEN_DEFAULT_SYSTEM_MESSAGE')

        # 记忆配置
        config.memory.enabled = os.getenv('QIANWEN_MEMORY_ENABLED', 'true').lower() == 'true'
        config.memory.storage_type = os.getenv('QIANWEN_MEMORY_STORAGE', config.memory.storage_type)
        config.memory.mongo_uri = os.getenv('MONGO_URI', config.memory.mongo_uri)
        config.memory.mongo_database = os.getenv('MONGO_DATABASE', config.memory.mongo_database)
        config.memory.max_history_length = int(os.getenv('QIANWEN_MAX_HISTORY', config.memory.max_history_length))
        return config

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'QianwenConfig':
        """从字典创建配置"""
        config = cls()

        if 'api' in config_dict:
            api_config = config_dict['api']
            config.api = APIConfig(**api_config)

        if 'model' in config_dict:
            model_config = config_dict['model']
            config.model = ModelConfig(**model_config)

        if 'memory' in config_dict:
            memory_config = config_dict['memory']
            config.memory = MemoryConfig(**memory_config)

        return config

    @classmethod
    def from_file(cls, config_file: str) -> 'QianwenConfig':
        """从配置文件创建配置"""
        with open(config_file, 'r', encoding='utf-8') as f:
            if config_file.endswith('.json'):
                config_dict = json.load(f)
            else:
                # 支持其他格式，如YAML
                raise ValueError(f"不支持的配置文件格式: {config_file}")

        return cls.from_dict(config_dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'api': {
                'api_key': self.api.api_key,
                'base_url': self.api.base_url,
                'timeout': self.api.timeout,
                'max_retries': self.api.max_retries,
                'retry_delay': self.api.retry_delay
            },
            'model': {
                'default_model': self.model.default_model,
                'default_temperature': self.model.default_temperature,
                'default_max_tokens': self.model.default_max_tokens,
                'default_system_message': self.model.default_system_message,
                'available_models': self.model.available_models
            },
            'memory': {
                'enabled': self.memory.enabled,
                'storage_type': self.memory.storage_type,
                'max_history_length': self.memory.max_history_length,
                'ttl_hours': self.memory.ttl_hours,
                'mongo_uri': self.memory.mongo_uri,
                'mongo_database': self.memory.mongo_database,
                'mongo_collection': self.memory.mongo_collection,
                'redis_host': self.memory.redis_host,
                'redis_port': self.memory.redis_port,
                'redis_db': self.memory.redis_db,
                'file_storage_path': self.memory.file_storage_path
            }
        }

    def save_to_file(self, config_file: str) -> None:
        """保存配置到文件"""
        config_dict = self.to_dict()

        with open(config_file, 'w', encoding='utf-8') as f:
            if config_file.endswith('.json'):
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            else:
                raise ValueError(f"不支持的配置文件格式: {config_file}")


class MongoMemoryStorage(MemoryStorage):
    """MongoDB记忆存储实现"""

    def __init__(self, config: MemoryConfig):
        self.config = config
        self._client = None
        self._collection = None

    def initialize(self) -> bool:
        """初始化MongoDB连接"""
        try:
            from pymongo import MongoClient
            self._client = MongoClient(self.config.mongo_uri)
            db = self._client[self.config.mongo_database]
            self._collection = db[self.config.mongo_collection]

            # 创建索引
            self._collection.create_index([("user_id", 1), ("session_id", 1), ("timestamp", -1)])

            # 设置TTL索引
            if self.config.ttl_hours > 0:
                self._collection.create_index(
                    "timestamp",
                    expireAfterSeconds=self.config.ttl_hours * 3600
                )

            return True
        except Exception as e:
            print(f"MongoDB记忆存储初始化失败: {e}")
            return False

    def save_message(self, user_id: str, session_id: str, role: str, content: str,
                     metadata: Dict[str, Any] = None) -> bool:
        """保存消息"""
        if self._collection is None:
            return False

        try:
            document = {
                "user_id": user_id,
                "session_id": session_id,
                "role": role,
                "content": content,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow()
            }

            self._collection.insert_one(document)
            return True
        except Exception as e:
            print(f"保存消息失败: {e}")
            return False

    def get_history(self, user_id: str, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取历史记录"""
        if self._collection is None:
            return []

        try:
            query = {"user_id": user_id, "session_id": session_id}
            cursor = self._collection.find(query).sort("timestamp", 1)

            if limit:
                cursor = cursor.limit(limit)
            elif self.config.max_history_length > 0:
                cursor = cursor.limit(self.config.max_history_length)

            messages = []
            for doc in cursor:
                messages.append({
                    "role": doc["role"],
                    "content": doc["content"],
                    "metadata": doc.get("metadata", {}),
                    "timestamp": doc["timestamp"]
                })

            return messages
        except Exception as e:
            print(f"获取历史记录失败: {e}")
            return []

    def clear_history(self, user_id: str, session_id: str) -> bool:
        """清除历史记录"""
        if self._collection is None:
            return False

        try:
            query = {"user_id": user_id, "session_id": session_id}
            self._collection.delete_many(query)
            return True
        except Exception as e:
            print(f"清除历史记录失败: {e}")
            return False

    def close(self) -> None:
        """关闭连接"""
        if self._client:
            self._client.close()
