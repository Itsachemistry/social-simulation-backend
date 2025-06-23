"""
LLM服务模块
支持ModelScope SDK和Mock模式
"""

import os
from typing import Optional, Dict, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMService:
    """LLM服务连接器"""
    
    def __init__(self, 
                 model_name: str = "qwen/Qwen2.5-0.5B-Instruct",
                 use_mock: bool = True,
                 api_key: Optional[str] = None):
        """
        初始化LLM服务
        
        Args:
            model_name: ModelScope模型名称
            use_mock: 是否使用Mock模式
            api_key: API密钥（如果需要）
        """
        self.model_name = model_name
        self.use_mock = use_mock
        self.api_key = api_key
        
        # ModelScope相关
        self.model = None
        self.tokenizer = None
        
        if not use_mock:
            self._initialize_modelscope()
        else:
            logger.info("使用Mock LLM服务")
    
    def _initialize_modelscope(self):
        """初始化ModelScope模型"""
        try:
            from modelscope import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            logger.info(f"正在加载ModelScope模型: {self.model_name}")
            
            # 加载tokenizer和模型
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, 
                trust_remote_code=True
            )
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True
            )
            
            logger.info("ModelScope模型加载完成")
            
        except ImportError:
            logger.error("ModelScope SDK未安装，请运行: pip install modelscope")
            self.use_mock = True
        except Exception as e:
            logger.error(f"ModelScope模型加载失败: {e}")
            self.use_mock = True
    
    def generate_post(self, prompt: str, max_length: int = 200) -> str:
        """
        生成帖子内容
        
        Args:
            prompt: 提示词
            max_length: 最大生成长度
            
        Returns:
            str: 生成的帖子内容
        """
        if self.use_mock:
            return self._mock_generate(prompt)
        else:
            return self._modelscope_generate(prompt, max_length)
    
    def _modelscope_generate(self, prompt: str, max_length: int) -> str:
        """使用ModelScope生成内容"""
        try:
            import torch
            
            # 构建输入
            inputs = self.tokenizer(prompt, return_tensors="pt")
            
            # 生成参数
            generation_config = {
                "max_new_tokens": max_length,
                "temperature": 0.7,
                "top_p": 0.9,
                "do_sample": True,
                "pad_token_id": self.tokenizer.eos_token_id
            }
            
            # 生成
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    **generation_config
                )
            
            # 解码输出
            generated_text = self.tokenizer.decode(
                outputs[0], 
                skip_special_tokens=True
            )
            
            # 提取新生成的内容（去掉原始prompt）
            new_content = generated_text[len(prompt):].strip()
            
            # 如果生成为空，返回默认内容
            if not new_content:
                return self._mock_generate(prompt)
            
            return new_content
            
        except Exception as e:
            logger.error(f"ModelScope生成失败: {e}")
            return self._mock_generate(prompt)
    
    def _mock_generate(self, prompt: str) -> str:
        """Mock生成内容"""
        # 基于提示词中的关键词生成内容
        if "政治" in prompt:
            return "关于这个话题，我认为需要理性讨论，各方都应该保持开放态度。"
        elif "娱乐" in prompt:
            return "哈哈，这个确实很有趣！大家觉得怎么样？"
        elif "科技" in prompt:
            return "科技发展确实很快，但也要注意平衡发展。"
        elif "体育" in prompt:
            return "运动精神很重要，希望大家都积极参与！"
        elif "经济" in prompt:
            return "经济发展需要各方共同努力，期待更好的未来。"
        elif "健康" in prompt:
            return "健康是最重要的，大家都要注意身体！"
        else:
            return "这个话题很有意思，值得深入讨论。"
    
    def switch_to_mock(self):
        """切换到Mock模式"""
        self.use_mock = True
        logger.info("已切换到Mock模式")
    
    def switch_to_modelscope(self):
        """切换到ModelScope模式"""
        if self.model is None:
            self._initialize_modelscope()
        else:
            self.use_mock = False
            logger.info("已切换到ModelScope模式")


class LLMServiceFactory:
    """LLM服务工厂类"""
    
    @staticmethod
    def create_service(config: Dict[str, Any]) -> LLMService:
        """
        创建LLM服务实例
        
        Args:
            config: 配置字典
            
        Returns:
            LLMService: LLM服务实例
        """
        model_name = config.get("model_name", "qwen/Qwen2.5-0.5B-Instruct")
        use_mock = config.get("use_mock", True)
        api_key = config.get("api_key")
        
        return LLMService(
            model_name=model_name,
            use_mock=use_mock,
            api_key=api_key
        ) 