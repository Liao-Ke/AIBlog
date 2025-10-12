import json
import os
import random
import time
import logging
from datetime import datetime
from functools import wraps

from cozepy import Coze, TokenAuth, COZE_CN_BASE_URL
from dotenv import load_dotenv

from utils import save_file, generate_random_filename


# --- 新增：日志和敏感信息处理函数 ---

def mask_sensitive_data(data: str, visible_chars: int = 1) -> str:
    """
    对敏感字符串进行脱敏处理，只显示前几位和后几位。
    例如: "735e8a9b1c2d" -> "735e***1c2d"
    """
    if not data or len(data) <= visible_chars * 2:
        return "***"
    return f"{data[:visible_chars]}****{data[-visible_chars:]}"


def setup_logging():
    """
    配置日志系统，将日志同时输出到控制台和按日期归档的文件中。
    每次运行都会创建一个新的日志文件。
    """
    # 1. 创建日志目录结构: logs/YYYY-MM-DD/
    log_dir_base = "logs"
    today_str = datetime.now().strftime("%Y-%m-%d")
    log_dir = os.path.join(log_dir_base, today_str)
    os.makedirs(log_dir, exist_ok=True)

    # 2. 创建唯一的日志文件名: app_HHMMSS_<random>.log
    timestamp = datetime.now().strftime("%H%M%S")
    random_suffix = random.randint(1000, 9999)
    log_filename = f"app_{timestamp}_{random_suffix}.log"
    log_filepath = os.path.join(log_dir, log_filename)

    # 3. 配置logger
    _logger = logging.getLogger("CozeWorkflowRunner")
    _logger.setLevel(logging.INFO)  # 设置日志级别

    # 避免重复添加Handler
    if _logger.handlers:
        return _logger

    # 创建格式化器
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # 4. 创建并配置文件处理器
    file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
    file_handler.setFormatter(formatter)
    _logger.addHandler(file_handler)

    # 5. 创建并配置控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)

    _logger.info(f"日志系统初始化完成，日志文件保存在: {log_filepath}")
    return _logger


# --- 原有代码（保持不变） ---

# 重试装饰器
def retry_with_exponential_backoff(max_attempts=5, initial_delay=1, max_delay=180, exponential_base=2, jitter=True):
    """
    带有指数退避和抖动的重试装饰器

    参数:
        max_attempts: 最大重试次数
        initial_delay: 初始延迟时间（秒）
        max_delay: 最大延迟时间（秒）
        exponential_base: 指数基数
        jitter: 是否添加随机抖动避免惊群效应
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as err:
                    attempts += 1
                    if attempts == max_attempts:
                        # 使用logger.error记录最终失败
                        logger.error(f"操作失败，已达到最大重试次数 {max_attempts}，最后一次异常: {str(err)}")
                        raise

                    # 计算指数退避延迟
                    delay = initial_delay * (exponential_base ** (attempts - 1))
                    delay = min(delay, max_delay)
                    if jitter:
                        delay = delay * (0.5 + random.random())

                    # 使用logger.warning记录重试信息
                    logger.warning(f"操作失败: {str(err)}，{delay:.2f}秒后进行第{attempts + 1}次重试...")
                    time.sleep(delay)

            return None

        return wrapper

    return decorator


# --- 主要逻辑函数 ---

def main():
    """主执行函数"""
    # initialize client
    load_dotenv()
    coze_api_token = os.getenv("COZE_API_TOKEN")
    coze_api_base = COZE_CN_BASE_URL
    coze = Coze(auth=TokenAuth(coze_api_token), base_url=coze_api_base)

    @retry_with_exponential_backoff(max_attempts=5, initial_delay=15)
    def create_workflow_run(_workflow_id):
        """创建工作流运行，带有重试机制"""
        return coze.workflows.runs.create(workflow_id=_workflow_id)

    try:
        # 获取工作流ID并创建运行实例，最多重试3次
        workflow_id = os.getenv("WORKFLOW_ID")
        if not workflow_id:
            raise ValueError("环境变量中未找到WORKFLOW_ID")

        # 对敏感信息进行脱敏
        masked_workflow_id = mask_sensitive_data(workflow_id)
        logger.info(f"开始执行工作流，ID: {masked_workflow_id}")

        ct = create_workflow_run(workflow_id)

        # 对调试URL中的敏感信息进行过滤
        debug_url = ct.debug_url
        sanitized_debug_url = debug_url.replace(workflow_id, masked_workflow_id)
        logger.info(f"工作流运行调试URL: {sanitized_debug_url}")

        # 处理返回结果
        ct_data = json.loads(ct.data)
        output = ct_data["output"]

        # 保存结果到文件
        file_name = generate_random_filename(extension="md")
        save_file(f"content/posts/TrialRun/{file_name}", output)
        logger.info(f"成功保存结果到文件: {file_name}")

    except Exception as e:
        # 使用logger.exception记录完整的错误堆栈
        logger.exception(f"脚本执行失败: {str(e)}")


if __name__ == "__main__":
    # 在脚本开始时初始化日志
    logger = setup_logging()
    # 执行主函数
    main()
