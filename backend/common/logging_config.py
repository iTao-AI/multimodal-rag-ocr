"""
统一日志配置 - 结构化日志

用法:
    from common.logging_config import setup_logging
    setup_logging("rag-chat")  # 或其他服务名
"""
import logging
import sys


def setup_logging(service_name: str, level: str = "INFO"):
    """设置结构化日志

    Args:
        service_name: 服务名称，会出现在每条日志中
        level: 日志级别，默认 INFO
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    log_format = f"%(asctime)s [{service_name}] %(levelname)s %(name)s: %(message)s"

    # 只在根 logger 还未配置 handler 时初始化（避免重复配置）
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.StreamHandler(sys.stdout),
            ],
        )
    else:
        root.setLevel(log_level)
        for handler in root.handlers:
            handler.setFormatter(logging.Formatter(log_format))

    # 设置第三方库日志级别为 WARNING，减少噪声
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
