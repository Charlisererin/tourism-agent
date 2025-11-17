# -*- coding: utf-8 -*-
import base64
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

from dotenv import load_dotenv
from openai import OpenAI  # 改为同步客户端

from .config import (
    QianwenConfig, MemoryConfig, MemoryStorage, MongoMemoryStorage
)

load_dotenv()


class QianwenAPIError(Exception):
    """千问API异常"""

    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.error_code = error_code
        self.message = message


@dataclass
class ChatMessage:
    """聊天消息数据类"""
    role: str
    content: Union[str, List[Dict[str, Any]]]
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class StorageFactory:
    """存储工厂类"""

    @staticmethod
    def create_memory_storage(config: MemoryConfig) -> Optional[MemoryStorage]:
        """创建记忆存储实例"""
        if not config.enabled:
            return None

        if config.custom_storage:
            return config.custom_storage

        if config.storage_type == "mongodb":
            return MongoMemoryStorage(config)
        elif config.storage_type == "redis":
            # 这里可以实现Redis存储
            raise NotImplementedError("Redis存储尚未实现，请使用自定义存储")
        elif config.storage_type == "file":
            # 这里可以实现文件存储
            raise NotImplementedError("文件存储尚未实现，请使用自定义存储")
        else:
            raise ValueError(f"不支持的存储类型: {config.storage_type}")


class MemoryManager:
    """记忆管理器 - 使用可配置的存储后端"""

    def __init__(self, config: MemoryConfig):
        self.config = config
        self.storage = StorageFactory.create_memory_storage(config)
        self._local_cache = None

    def initialize(self):
        """初始化记忆管理器"""
        if self.storage:
            return self.storage.initialize()
        return True

    def save_message(self, message: ChatMessage):
        """保存消息到记忆"""
        if not self.storage:
            return

        try:
            # 保存到存储
            self.storage.save_message(
                user_id=message.user_id,
                session_id=message.session_id,
                role=message.role,
                content=message.content if isinstance(message.content, str) else json.dumps(message.content),
                metadata=message.metadata
            )

            # 更新本地缓存
            if self._local_cache:
                cache_key = f"{message.user_id}:{message.session_id}"
                if cache_key in self._local_cache:
                    self._local_cache[cache_key].append(message)

        except Exception as e:
            print(f"保存消息到记忆失败: {e}")

    def get_history(self, user_id: str, session_id: str, limit: int = None) -> List[ChatMessage]:
        """获取历史记录"""
        if not self.storage:
            return []

        try:
            # 检查本地缓存
            cache_key = f"{user_id}:{session_id}"
            if self._local_cache and cache_key in self._local_cache:
                cached_messages = self._local_cache[cache_key]
                if limit:
                    return cached_messages[-limit:]
                return cached_messages

            # 从存储获取
            messages_data = self.storage.get_history(user_id, session_id, limit)

            messages = []
            for msg_data in messages_data:
                content = msg_data['content']
                try:
                    # 尝试解析JSON内容
                    content = json.loads(content)
                except (json.JSONDecodeError, TypeError):
                    # 如果不是JSON，保持原样
                    pass

                message = ChatMessage(
                    role=msg_data['role'],
                    content=content,
                    timestamp=msg_data.get('timestamp', datetime.now()),
                    user_id=user_id,
                    session_id=session_id,
                    metadata=msg_data.get('metadata', {})
                )
                messages.append(message)

            # 更新本地缓存
            if self._local_cache:
                self._local_cache[cache_key] = messages

            return messages

        except Exception as e:
            print(f"获取历史记录失败: {e}")
            return []

    def close(self):
        """关闭记忆管理器"""
        if self.storage:
            self.storage.close()


class QianwenChat:
    """千问对话会话类 - 支持链式调用"""

    def __init__(self, client: 'QianwenClient', user_id: str = None, session_id: str = None):
        self.client = client
        self._user_id = user_id or "default_user"
        self._session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 链式调用参数
        self._model = client.config.model.default_model
        self._temperature = client.config.model.default_temperature
        self._max_tokens = client.config.model.default_max_tokens
        self._system_message = client.config.model.default_system_message
        self._search_enabled = False
        self._memory_enabled = client.config.memory.enabled

    def model(self, model_name: str) -> 'QianwenChat':
        """设置模型"""
        self._model = model_name
        return self

    def ask(self, message: str, **kwargs) -> Dict[str, Any]:
        """发送消息并获取回复"""
        try:
            # 构建消息列表
            messages = self._build_messages(message)

            # 构建请求参数
            request_params = {
                "model": self._model,
                "messages": messages,
                "temperature": self._temperature,
                "max_tokens": self._max_tokens,
                **kwargs
            }

            # 添加搜索工具
            if self._search_enabled:
                request_params["tools"] = [{
                    "type": "web_search",
                    "web_search": {"enable": True}
                }]

            # 发送请求
            response = self.client.sync_client.chat.completions.create(**request_params)
            response_dict = response.model_dump()

            # 保存对话到记忆
            if self._memory_enabled and self.client.memory_manager:
                # 保存用户消息
                user_message = ChatMessage(
                    role="user",
                    content=message,
                    user_id=self._user_id,
                    session_id=self._session_id
                )
                self.client.memory_manager.save_message(user_message)

                # 保存助手回复
                if response_dict.get('choices'):
                    assistant_content = response_dict['choices'][0]['message']['content']
                    assistant_message = ChatMessage(
                        role="assistant",
                        content=assistant_content,
                        user_id=self._user_id,
                        session_id=self._session_id
                    )
                    self.client.memory_manager.save_message(assistant_message)

            return response_dict

        except Exception as e:
            raise QianwenAPIError(f"API调用失败: {e}")

    def image(self, message: str, image_path: str, **kwargs) -> Dict[str, Any]:
        """图像理解"""
        if not os.path.exists(image_path):
            raise QianwenAPIError(f"图片文件不存在: {image_path}")

        # 编码图片
        image_base64 = self.client._encode_image(image_path)

        # 构建多模态消息
        multimodal_message = [
            {"type": "text", "text": message},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_base64}"
                }
            }
        ]

        return self._multimodal_request(multimodal_message, **kwargs)

    def video(self, message: str, video_frames: List[str], **kwargs) -> Dict[str, Any]:
        """视频理解"""
        # 构建多模态消息
        multimodal_message = [{"type": "text", "text": message}]

        for frame_path in video_frames:
            if not os.path.exists(frame_path):
                raise QianwenAPIError(f"视频帧文件不存在: {frame_path}")

            frame_base64 = self.client._encode_image(frame_path)
            multimodal_message.append({
                "type": "video_url",
                "video_url": {
                    "url": f"data:video/mp4;base64,{frame_base64}"
                }
            })

        return self._multimodal_request(multimodal_message, **kwargs)

    def _multimodal_request(self, content: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """多模态请求的通用方法"""
        try:
            # 获取历史记录
            messages = []
            if self._memory_enabled and self.client.memory_manager:
                history = self.client.memory_manager.get_history(
                    self._user_id, self._session_id,
                    limit=self.client.config.memory.max_history_length
                )

                for msg in history:
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })

            # 添加系统消息
            if self._system_message:
                messages.insert(0, {
                    "role": "system",
                    "content": self._system_message
                })

            # 添加当前多模态消息
            messages.append({
                "role": "user",
                "content": content
            })

            # 构建请求参数
            request_params = {
                "model": self._model,
                "messages": messages,
                "temperature": self._temperature,
                "max_tokens": self._max_tokens,
                **kwargs
            }

            # 发送请求
            response = self.client.sync_client.chat.completions.create(**request_params)
            response_dict = response.model_dump()

            # 保存对话到记忆
            if self._memory_enabled and self.client.memory_manager:
                # 保存用户消息
                user_message = ChatMessage(
                    role="user",
                    content=content,
                    user_id=self._user_id,
                    session_id=self._session_id
                )
                self.client.memory_manager.save_message(user_message)

                # 保存助手回复
                if response_dict.get('choices'):
                    assistant_content = response_dict['choices'][0]['message']['content']
                    assistant_message = ChatMessage(
                        role="assistant",
                        content=assistant_content,
                        user_id=self._user_id,
                        session_id=self._session_id
                    )
                    self.client.memory_manager.save_message(assistant_message)

            return response_dict

        except Exception as e:
            raise QianwenAPIError(f"多模态API调用失败: {e}")

    def _build_messages(self, message: str) -> List[Dict[str, Any]]:
        """构建消息列表"""
        messages = []

        # 添加系统消息
        if self._system_message:
            messages.append({
                "role": "system",
                "content": self._system_message
            })

        # 获取历史记录
        if self._memory_enabled and self.client.memory_manager:
            history = self.client.memory_manager.get_history(
                self._user_id, self._session_id,
                limit=self.client.config.memory.max_history_length
            )

            for msg in history:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        # 添加当前消息
        messages.append({
            "role": "user",
            "content": message
        })

        return messages

    def get_history(self, limit: int = None) -> List[ChatMessage]:
        """获取历史记录"""
        if self.client.memory_manager:
            return self.client.memory_manager.get_history(self._user_id, self._session_id, limit)
        return []


class QianwenClient:
    """千问客户端 - 增强版"""

    def __init__(self, config: Union[QianwenConfig, Dict[str, Any], str] = None, **kwargs):
        # 处理配置
        if config is None:
            self.config = QianwenConfig.from_env()
        elif isinstance(config, str):
            self.config = QianwenConfig.from_file(config)
        elif isinstance(config, dict):
            self.config = QianwenConfig.from_dict(config)
        elif isinstance(config, QianwenConfig):
            self.config = config
        else:
            raise ValueError("配置参数类型错误")

        # 应用kwargs覆盖配置
        if 'api_key' in kwargs:
            self.config.api.api_key = kwargs['api_key']
        if 'base_url' in kwargs:
            self.config.api.base_url = kwargs['base_url']

        # 检查API密钥
        if not self.config.api.api_key:
            raise QianwenAPIError("未设置API密钥，请设置QIANWEN_API_KEY环境变量或在配置中指定")

        # 初始化OpenAI客户端（同步）
        self.sync_client = OpenAI(
            api_key=self.config.api.api_key,
            base_url=self.config.api.base_url,
            timeout=self.config.api.timeout
        )

        # 初始化管理器
        self.memory_manager = None

    def initialize(self):
        """初始化客户端"""
        # 初始化记忆管理器
        if self.config.memory.enabled:
            self.memory_manager = MemoryManager(self.config.memory)
            self.memory_manager.initialize()

    def chat(self, user_id: str = None, session_id: str = None) -> QianwenChat:
        """创建对话会话"""
        return QianwenChat(self, user_id, session_id)

    def _encode_image(self, image_path: str) -> str:
        """编码图片为base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def close(self):
        """关闭客户端"""
        if self.memory_manager:
            self.memory_manager.close()
        self.sync_client.close()

    def __enter__(self):
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def create_client(config: Union[QianwenConfig, Dict[str, Any], str] = None, **kwargs) -> QianwenClient:
    """创建同步千问客户端"""
    return QianwenClient(config, **kwargs)
