# ModelScope集成使用指南

## 概述

本项目已集成ModelScope SDK，支持使用本地模型进行文本生成。目前支持Mock模式和ModelScope模式两种运行方式。

## 安装依赖

### 1. 安装ModelScope SDK

```bash
pip install modelscope
pip install torch torchvision torchaudio
```

### 2. 可选：安装CUDA支持（如果有GPU）

```bash
# 根据你的CUDA版本选择对应的torch版本
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## 配置说明

### 1. 模型选择

推荐使用的轻量级模型：
- `qwen/Qwen2.5-0.5B-Instruct` (推荐，0.5B参数，速度快)
- `qwen/Qwen2.5-1.5B-Instruct` (1.5B参数，质量更好)
- `qwen/Qwen2.5-3B-Instruct` (3B参数，质量最佳但较慢)

### 2. 配置文件设置

在`main.py`中修改配置：

```python
config = {
    "posts_per_slice": 10,
    
    # LLM配置
    "llm": {
        "model_name": "qwen/Qwen2.5-0.5B-Instruct",  # 模型名称
        "use_mock": False,  # 设置为False使用ModelScope
        "api_key": None
    },
    
    "agent_config_path": "config/agents.json"
}
```

## 使用方式

### 1. Mock模式（推荐用于开发调试）

```python
config = {
    "llm": {
        "model_name": "qwen/Qwen2.5-0.5B-Instruct",
        "use_mock": True,  # 使用Mock模式
        "api_key": None
    }
}
```

**优点：**
- 启动速度快
- 不消耗GPU资源
- 适合开发和调试

### 2. ModelScope模式（推荐用于正式运行）

```python
config = {
    "llm": {
        "model_name": "qwen/Qwen2.5-0.5B-Instruct",
        "use_mock": False,  # 使用ModelScope模式
        "api_key": None
    }
}
```

**优点：**
- 生成内容更真实
- 支持复杂的语言理解
- 可以生成多样化的内容

## 运行示例

### 1. 使用Mock模式

```bash
python main.py
```

### 2. 使用ModelScope模式

```bash
# 首次运行会下载模型（约1GB）
python main.py
```

### 3. 使用配置文件

```bash
python test_with_config.py
```

## 性能优化建议

### 1. 模型选择
- **开发阶段**：使用Mock模式
- **测试阶段**：使用0.5B模型
- **生产阶段**：使用1.5B或3B模型

### 2. 硬件要求
- **CPU模式**：至少8GB内存
- **GPU模式**：至少4GB显存（推荐8GB+）

### 3. 生成参数调整

在`src/llm_service.py`中可以调整生成参数：

```python
generation_config = {
    "max_new_tokens": max_length,  # 最大生成长度
    "temperature": 0.7,            # 温度（0.1-1.0，越高越随机）
    "top_p": 0.9,                  # 核采样参数
    "do_sample": True,             # 是否使用采样
    "pad_token_id": self.tokenizer.eos_token_id
}
```

## 故障排除

### 1. 模型下载失败
```bash
# 手动下载模型
python -c "from modelscope import AutoTokenizer; AutoTokenizer.from_pretrained('qwen/Qwen2.5-0.5B-Instruct')"
```

### 2. 内存不足
- 使用更小的模型（0.5B）
- 减少batch_size
- 使用CPU模式

### 3. 显存不足
- 使用CPU模式
- 使用更小的模型
- 减少max_new_tokens

## 下一步计划

1. **支持更多模型**：集成更多ModelScope模型
2. **批量生成**：支持批量处理多个Agent的生成请求
3. **缓存机制**：添加模型缓存，避免重复加载
4. **API模式**：支持远程API调用模式

## 注意事项

1. **首次运行**：ModelScope模式首次运行会下载模型，需要较长时间
2. **资源消耗**：ModelScope模式会消耗较多内存和GPU资源
3. **网络要求**：需要稳定的网络连接下载模型
4. **存储空间**：模型文件较大，确保有足够存储空间 