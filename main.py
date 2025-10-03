import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from cozepy import Coze, TokenAuth, COZE_CN_BASE_URL
from dotenv import load_dotenv

from utils import save_file, generate_random_filename

# initialize client
load_dotenv()
coze_api_token = os.getenv("COZE_API_TOKEN")
coze_api_base = COZE_CN_BASE_URL
coze = Coze(auth=TokenAuth(coze_api_token), base_url=coze_api_base)

ct = coze.workflows.runs.create(workflow_id=os.getenv("WORKFLOW_ID"), parameters=json.loads("""{
    "input": [
        "生活趣事",
        "每周日记",
        "观点与人文思考",
        "每日计划"
    ]
}"""))

ct_data = json.loads(ct.data)
print(ct.model_dump_json(), ct.data)
output = json.loads(ct_data["output"])
output1 = json.loads(ct_data["output1"])
output2 = ct_data["output2"]
output3 = json.loads(ct_data["output3"])

tz_aware_datetime = datetime.now(ZoneInfo('Asia/Shanghai'))
iso_with_tz = tz_aware_datetime.isoformat(timespec='seconds')

file_name = generate_random_filename(extension="md")
file_content = f"""---
title: {output["title"]}
description: {output["description"]}
summary: {output["summary"]}
tags: {output1["tags"]}
categories: ["试运行"]
date: {iso_with_tz}
AIGC: true
cover:
  image: "{output3["data"]["image_url"]}"
  # can also paste direct link from external site
  # ex. https://i.ibb.co/K0HVPBd/paper-mod-profilemode.png
  alt: "{output3["data"]["description"]}"
  caption: "{output3["data"]["title"]}"
  relative: false # To use relative path for cover image, used in hugo Page-bundles
---
{output2}
"""
save_file(f"content/posts/TrialRun/{file_name}", file_content)
