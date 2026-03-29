import os
import sys
import toml
import utils
from colorama import init,Fore,Style

BANNER="""
  ________   __  _______ _____            _   _  _____ _            _______ ____  _____  
 |  ____\ \ / / |__   __|  __ \     /\   | \ | |/ ____| |        /\|__   __/ __ \|  __ \ 
 | |__   \ V /     | |  | |__) |   /  \  |  \| | (___ | |       /  \  | | | |  | | |__) |
 |  __|   > <      | |  |  _  /   / /\ \ | . ` |\___ \| |      / /\ \ | | | |  | |  _  / 
 | |____ / . \     | |  | | \ \  / ____ \| |\  |____) | |____ / ____ \| | | |__| | | \ \ 
 |______/_/ \_\    |_|  |_|  \_\/_/    \_\_| \_|_____/|______/_/    \_\_|  \____/|_|  \_\
 | |                                                                                     
 | |__  _   _    ___  _ __  _ __  _ __ ___                                               
 | '_ \| | | |  / _ \| '_ \| '_ \| '__/ __|                                              
 | |_) | |_| | | (_) | | | | |_) | |  \__ \                                              
 |_.__/ \__, |  \___/|_| |_| .__/|_|  |___/                                              
         __/ |             | |                                                           
        |___/              |_|                                                                                                                                     
"""

CONFIG="config.toml"
DEFAULT_CONFIG = r"""
VERSION = "v1.0"

#输入与输出KS文件的父级目录地址
[PATH]
input_path = "./input_path"
output_path = "./output"
backup_path = "./backup_progress"

#各种最大值的设置和杂项
[SYSTEM]
#单批次的最大文本块数
batch_size = 8
#最大并行数
max_threads = 20
#最大重试次数
max_retrys = 10
#传给llm的文本块分隔符
separator = "\n===line===\n"
progress_file = "translation_progress.json"

#LLM模型的相关设置
[LLM]
api_key = ""
base_url = ""
model_name = ""
#示例提示词
prompt = f'''
你是一名资深的 Type-Moon 视觉小说本地化汉化专家，尤其精通奈须蘑菇（Nasu Kinoko）的文风。你的任务是将输入的日文文本精准、生动地翻译成中文。当前正在翻译的作品是《Fate/hollow ataraxia》。

【程序绝对铁律 —— 违反将导致编译脚本崩溃与死循环】：
1. 批处理分割符：输入的文本由多个文本块组成，块与块之间使用 `{separator}` 作为强制分割符。你必须在译文中【原样输出】所有的分割符，不能多也不能少！翻译后的文本块数量必须与原文完全一致。
2. 行数对齐（极其重要）：必须绝对保留每个块内部的换行结构！严禁漏译、吃句或合句！原文有几行，译文该块就必须有几行！即便原文是一句简短的吐槽或毫无意义的感叹，也【绝对不允许】擅自忽略或跳过！即使是极短行也必须保留为独立一行，绝不能省略。例如「は？」「え？」「……」这类1~3字符行，也必须单独输出一行。
3. 占位符保留：原文中的大多特殊标记和引擎代码已被替换为形如 `<T0>`, `<T1>` 的占位符，对于不可见的占位符也必须保留。这些是极其重要的底层代码，【绝对不可】修改、删除、遗漏或翻译它们，请将其原封不动地保留在译文的对应位置。
4. 排版铁律：务必原样保留原文中的日文直角引号「」和『』，绝对不可将其本地化为中文的双引号“”或单引号‘’。

【FHA 翻译语境与文风指导】：
1. 区分双重语境：《Fate/hollow ataraxia》分为“平稳的日常篇”与“悬疑的夜间篇”。日常旁白与对话请保持轻小说般细腻、幽默、极其生动的口语化（凸显角色的傲娇、毒舌、天然等属性）；一旦进入夜间暗线或战斗阶段，请立刻切换为奈须蘑菇特有的晦涩、细腻、充满中二与文学性的史诗感文风。
2. 原汁原味：保留二次元表达习惯与称呼词汇（如自然地使用“前辈”、“Master”、“Servant”等），拒绝生硬的书面语机翻味。
3. 忠于原著张力：原作包含深刻、激烈甚至直白粗俗的剧情描写。请忠实于原著的情感色彩和艺术张力，绝对不要随意删减、软化词汇或进行自我阉割。
4. 彻底消除假名残留（极其重要）：绝对不允许在最终的中文译文中保留任何日文假名！遇到日文的语气词、拟声词、叹词、口癖（如「あー」、「えっと」、「くっ」、「ふふ」等），请务必根据语境将其本地化为对应的中文汉字（如“啊——”、“那个”、“唔”、“呵呵”等），绝对不能直接照搬日文原文。
5. 视觉小说断句特性（极其重要）：Galgame 剧本中经常出现故意说到一半的半截话、倒装句或未完结的悬念句（例如原文以“将其……”、“就算这样，也”结尾）。这是游戏底层演出的需要，【绝对不可】因为句子看起来不完整就擅自删除、合并或补全！无论原文多像病句或半截话，都必须忠实地翻译出来并保留悬念感。

【Ruby 注音特殊处理】：
遇到未被掩盖的注音标签 `[ruby text="xxx"]` 时，【绝对不可】更改 "ruby" 和 "text=" 这两个底层英文字母，请按以下规则处理：
- 规则 A (双重含义词/型月设定)：如果是专有名词或中二设定，请严格保留标签结构，只翻译内容。例如原文 `幻想崩壊[ruby text="ブロークン・ファントム"]` -> 译为 `幻想崩坏[ruby text="Broken Phantasm"]`。
- 规则 B (冗余读音)：如果是对普通日文汉字的单纯假名注音（例如 `蝶[ruby text="つがい"]番`），中文语境下不需要注音，请直接删除整个 ruby 标签，只输出流畅的中文主体（如 `门轴`）。

【输出格式要求】：
只输出包含分割符的纯文本翻译结果，绝对不要使用任何代码块（如 ```），不要使用 XML/HTML 标签，也不要包含任何解释或废话！
'''

"""

def write_default_config():
    """
    写入默认配置文件
    """
    with open(CONFIG,'w',encoding='utf-8') as f:
        f.write(DEFAULT_CONFIG)

def load_config():
    """
    程序第一个被调用的函数
    加载配置文件，如果没有就写入默认配置
    """
    while True:
        utils.clear_panel()
        if not os.path.exists(CONFIG):
            print(f"未发现配置文件,生成中……\n")
            write_default_config()
            print(f"默认toml已写至{CONFIG},请修改并保存后键入q:",end='',flush=True)
            if utils.catch_keyboard(['q'])=='q':
                continue
        try:
            print("发现配置文件,尝试读取……\n")
            with open(CONFIG,'r',encoding='utf-8') as f:
                config=toml.load(f)
                print("读取成功\n")
                return config
        except Exception as e:
            print(f"读取配置文件失败,错误信息:{e}\n")
            print("[1] 初始化配置文件\n")
            print("[2] 如果你需要修改后重新加载而不是初始化\n")
            print("[0] 退出程序\n")
            print("请直接输入数字0~2:",end='',flush=True)
            choice=utils.catch_keyboard(['0','1','2'])
            if choice=='1':
                write_default_config()
                print("已初始化配置文件\n")
                utils.press_to_continue()
            elif choice=='2':
                continue
            elif choice=='0':
                sys.exit(0)

def print_banner(CONFIG):
    """
    在终端中打印大！横！幅！
    """
    init(autoreset=True)
    print(Fore.LIGHTBLUE_EX+Style.BRIGHT+BANNER)
    print(Fore.CYAN+Style.BRIGHT+" "*30+"a automatical extractor and translator code by onprs>>>version:"+CONFIG["VERSION"])
    print(Fore.WHITE+" "*28+"--------------------------------------\n")
    utils.press_to_continue()

def get_config():
    """
    将读取出来的配置文件以字典的方式传出去
    """
    LOAD_CONFIG=load_config()

    VERSION=LOAD_CONFIG.get("VERSION","")

    _path=LOAD_CONFIG.get("PATH",{})
    INPUT_PATH=_path.get("input_path","")
    OUTPUT_PATH=_path.get("output_path","")
    BACKUP_PATH=_path.get("backup_path","")

    _llm=LOAD_CONFIG.get("LLM",{})
    API_KEY=_llm.get("api_key","")
    BASE_URL=_llm.get("base_url","")
    MODLE_NAME=_llm.get("model_name","")
    PROMPT=_llm.get("prompt","")

    _system=LOAD_CONFIG.get("SYSTEM",{})
    PROGRESS_FILE=_system.get("progress_file","")
    BATCH_SIZE=_system.get("batch_size",0)
    MAX_THREADS=_system.get("max_threads",0)
    MAX_RETRYS=_system.get("max_retrys",0)
    SEPARATOR=_system.get("separator","")

    return {"VERSION":VERSION,"INPUT_PATH":INPUT_PATH,"OUTPUT_PATH":OUTPUT_PATH,"BACKUP_PATH":BACKUP_PATH,"API_KEY":API_KEY,"BASE_URL":BASE_URL,"MODLE_NAME":MODLE_NAME,"PROMPT":PROMPT,"PROGRESS_FILE":PROGRESS_FILE,"BATCH_SIZE":BATCH_SIZE,"MAX_THREADS":MAX_THREADS,"MAX_RETRYS":MAX_RETRYS,"SEPARATOR":SEPARATOR}

def print_information(CONFIG):
    """
    给用户输出各种配置信息
    """
    print(f"{"#"*40}\n输入路径:{CONFIG["INPUT_PATH"]}\n\n输出路径:{CONFIG["OUTPUT_PATH"]}\n")
    print(f"LLM调用地址:{CONFIG["BASE_URL"]}\n\n使用的模型ID名称:{CONFIG["MODLE_NAME"]}\n")
    print(f"单组文本块数量:{CONFIG["BATCH_SIZE"]}\n\n并发线程数量:{CONFIG["MAX_THREADS"]}\n\n最大失败尝试次数:{CONFIG["MAX_RETRYS"]}\n")
    print(f"LLM提示词中文本块分行标记:{CONFIG["SEPARATOR"].strip()}\n")
    print(f"LLM提示词:{CONFIG["PROMPT"]}\n")
    print(f"项目进度保存文件名称:{CONFIG["PROGRESS_FILE"]}\n")

