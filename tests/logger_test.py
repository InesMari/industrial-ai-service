import logging
logging.basicConfig(level=logging.INFO)   # ← 只多了这一行
logger = logging.getLogger(__name__)
logger.info("测试日志")