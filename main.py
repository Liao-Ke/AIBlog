import json
import os
import time
from functools import wraps

from cozepy import Coze, TokenAuth, COZE_CN_BASE_URL
from dotenv import load_dotenv

from utils import save_file, generate_random_filename


# 重试装饰器
def retry(max_attempts=3, delay_seconds=2):
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
                        raise  # 达到最大重试次数，抛出最后一次异常
                    print(f"操作失败: {str(err)}，将在{delay_seconds}秒后进行第{attempts + 1}次重试...")
                    time.sleep(delay_seconds)

        return wrapper

    return decorator


# initialize client
load_dotenv()
coze_api_token = os.getenv("COZE_API_TOKEN")
coze_api_base = COZE_CN_BASE_URL
coze = Coze(auth=TokenAuth(coze_api_token), base_url=coze_api_base)


@retry(max_attempts=3, delay_seconds=2)
def create_workflow_run(_workflow_id):
    """创建工作流运行，带有重试机制"""
    return coze.workflows.runs.create(workflow_id=_workflow_id)


try:
    # 获取工作流ID并创建运行实例，最多重试3次
    workflow_id = os.getenv("WORKFLOW_ID")
    if not workflow_id:
        raise ValueError("环境变量中未找到WORKFLOW_ID")

    ct = create_workflow_run(workflow_id)
    # 打印调试URL
    debug_url = ct.debug_url
    print(f"工作流运行调试URL: {debug_url}")

    # 处理返回结果
    ct_data = json.loads(ct.data)
    output = ct_data["output"]

    # 保存结果到文件
    file_name = generate_random_filename(extension="md")
    save_file(f"content/posts/TrialRun/{file_name}", output)
    print(f"成功保存结果到文件: {file_name}")

except Exception as e:
    print(f"执行失败: {str(e)}")
