from openai import OpenAI
from tqdm import tqdm

PROMPT=""
MODLE_NAME=""
client=None

def init_llm(CONFIG):
    """
    初始化llm的配置内容
    """
    global client,PROMPT,MODLE_NAME
    client=OpenAI(api_key=CONFIG["API_KEY"],base_url=CONFIG["BASE_URL"])
    PROMPT=CONFIG["PROMPT"]
    MODLE_NAME=CONFIG["MODLE_NAME"]

def call_llm(masked_text):
    """
    推送masked_text翻译内容给llm，将翻译结果返回给worker_task
    """
    system_prompt=PROMPT
    try:
        response=client.chat.completions.create(model=MODLE_NAME,messages=[{"role":"system","content":system_prompt},{"role":"user","content":masked_text}],temperature=1)
        tqdm.write(f"正在翻译源文本:\n====================\n{masked_text}\n====================\n")
        return response.choices[0].message.content
    except Exception as e:
        e_str=str(e)
        if "html" in e_str:
            tqdm.write(f"请求llm失败，你也许使用了网页逆向的api？但是请求超时了，等待重试……\n")
        else:
            tqdm.write(f"请求失败，错误信息:{e}，等待重试……\n")
        return None