from dotenv import load_dotenv
import os, requests

load_dotenv(".env")                          # 把 .env 里的键值读进环境变量
key = os.environ.get("DEEPSEEK_API_KEY")     # 参数是「名字」，拿到的是「值」
print("key 读到了吗:", bool(key), "长度:", len(key or ""))

url = "https://api.deepseek.com/chat/completions"
prompt = "用一句中文定性描述今天 A 股行业板块的行情，可以说普涨、普跌、分化、资金集中度强弱。不要出现任何数字、百分比、具体板块名。只输出这一句话，不要解释。"

resp = requests.post(
    url,
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]},
    timeout=30,
)

print("HTTP 状态码:", resp.status_code)
print("模型回复:", resp.json()["choices"][0]["message"]["content"])
