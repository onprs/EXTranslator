import os
import re
import sys
import uuid
import json
import toml
import time
import msvcrt
import shutil
import subprocess
#import charset_normalizer
import threading
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor,as_completed
from colorama import init,Back,Fore,Style
from openai import OpenAI

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
input_path = "C:/Users/liang/Desktop/expkg/source"
output_path = "./output"
backup_path = "./backup_progress"

#LLM模型的相关设置
[LLM]
api_key = "sk-7Nb8FwAmO5zvmEzwkHlBXWX5RaDycdkPAmeKZqT2Ql5cDEQQ"
base_url = "https://ai.wsocket.xyz/v1"
model_name = "gpt-5.4-xhigh"
prompt = '''
你是一名资深的 Type-Moon 视觉小说本地化汉化专家，尤其精通奈须蘑菇（Nasu Kinoko）的文风。你的任务是将输入的日文文本精准、生动地翻译成中文。当前正在翻译的作品是《Fate/hollow ataraxia》。

【程序绝对铁律 —— 违反将导致编译脚本崩溃与死循环】：
1. 批处理分割符：输入的文本由多个文本块组成，块与块之间使用 `\n===line===\n` 作为强制分割符。你必须在译文中【原样输出】所有的分割符，不能多也不能少！翻译后的文本块数量必须与原文完全一致。
2. 行数对齐（极其重要）：必须绝对保留每个块内部的换行结构！严禁漏译、吃句或合句！原文有几行，译文该块就必须有几行！即便原文是一句简短的吐槽或毫无意义的感叹，也【绝对不允许】擅自忽略或跳过！
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

#各种最大值的设置和杂项
[SYSTEM]
batch_size = 8
max_threads = 20
max_retrys = 10
separator = "\n===line===\n"
progress_file = "translation_progress.json"
"""

def clear_panel():
    subprocess.run('cls' if os.name=='nt' else 'clear',shell=True)

def press_to_continue():
    if os.name=='nt':
        subprocess.run('pause',shell=True)

def catch_keyboard(keys):
    while True:
        choice=msvcrt.getch().decode(encoding='utf-8',errors='ignore').strip()
        if choice in keys:
            print(choice)
            return choice
        
# def fix_windows_size(wide,high):
#     if (os.name=='nt'):
#         subprocess.run(f'mode con: cols={wide} lines={high}',shell=True)

def write_default_config():
    with open(CONFIG,'w',encoding='utf-8') as f:
        f.write(DEFAULT_CONFIG)

def load_config():
    while True:
        clear_panel()
        if not os.path.exists(CONFIG):
            print(f"未发现配置文件,生成中……\n")
            write_default_config()
            print(f"默认toml已写至{CONFIG},请修改并保存后键入q:",end='',flush=True)
            if catch_keyboard(['q'])=='q':
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
            choice=catch_keyboard(['0','1','2'])
            if choice=='1':
                write_default_config()
                print("已初始化配置文件\n")
                press_to_continue()
            elif choice=='2':
                continue
            elif choice=='0':
                sys.exit(0)

# fix_windows_size(1920,1080)
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

client=OpenAI(api_key=API_KEY,base_url=BASE_URL)
save_lock=threading.Lock()

def print_banner():
    init(autoreset=True)
    print(Fore.LIGHTBLUE_EX+Style.BRIGHT+BANNER)
    print(Fore.CYAN+Style.BRIGHT+" "*30+"a automatical extractor and translator code by onprs>>>version:"+VERSION)
    print(Fore.WHITE+" "*28+"--------------------------------------\n")
    press_to_continue()

def print_information():
    """
    给用户输出各种配置信息
    """
    print(f"{"#"*40}\n输入路径:{INPUT_PATH}\n\n输出路径:{OUTPUT_PATH}\n")
    print(f"LLM调用地址:{BASE_URL}\n\n使用的模型ID名称:{MODLE_NAME}\n")
    print(f"单组文本块数量:{BATCH_SIZE}\n\n并发线程数量:{MAX_THREADS}\n\n最大失败尝试次数:{MAX_RETRYS}\n")
    print(f"LLM提示词中文本块分行标记:{SEPARATOR.strip()}\n")
    print(f"LLM提示词:{PROMPT}\n")
    print(f"项目进度保存文件名称:{PROGRESS_FILE}\n")

def mask_text(original_text):
    """
    将[]行内标签使用<T*>进行替换
    """
    tag_pattern=re.compile(r'\[(?!ruby).*?\]')
    tags=tag_pattern.findall(original_text)
    masked_text=original_text
    tag_list={}
    for tag_pos,tag_text in enumerate(tags):
        place_text=f"<T{tag_pos}>"
        masked_text=masked_text.replace(tag_text,place_text,1)
        tag_list[place_text]=tag_text
    return masked_text,tag_list

def unmask_text(masked_text,tag_list):
    """
    将原替换<T*>换回原[]行内标签
    """
    final_text=masked_text
    for place_text,tag_text in tag_list.items():
        final_text=final_text.replace(place_text,tag_text)
    return final_text

def ex_ks(file_path):
    """
    主逻辑
    用charset_normalizer进行编码试探
    将原KS文件按文本块提取，并且传给mask_text清洗[]行内标签
    """
    with open(file_path,'rb') as f:
        raw_byte=f.read()
    #识别编码方式
    text_content=None
    readed_encoding=None
    for enc in ['utf-16le','utf-8','shiftjis']:
        try:
            text_content=raw_byte.decode(enc)
            readed_encoding=enc
            break
        except UnicodeDecodeError:
            continue
    if readed_encoding is None:
        print("该文件不是utf16le及utf8和shiftjis的任何一种\n")
    print(f"使用的编码:{readed_encoding}\n")
    lines=text_content.splitlines()
    ex_line=[]
    block_content=[]
    start_line=-1
    #分块提取
    for line_pos,line_text in enumerate(lines):
        clean_line=line_text.strip()
        is_end=(not clean_line)or clean_line.startswith(('@','*',';'))
        if is_end:
            if len(block_content)>0:
                content,tag_list=mask_text('\n'.join(block_content))
                ex_line.append({"start_line":start_line,"end_line":line_pos-1,"block_content":content,"tag_list":tag_list})
                block_content=[]
                start_line=-1
            continue
        if len(block_content)==0:
            start_line=line_pos
        block_content.append(line_text.rstrip()) 
    if len(block_content)>0:
        content,tag_list=mask_text('\n'.join(block_content))
        ex_line.append({"start_line":start_line,"end_line":len(lines)-1,"block_content":content,"tag_list":tag_list})
    return ex_line

def scan_all_ks_file(file_path):
    """
    扫描一个文件夹，提取文件夹下(包括子文件夹)的所有ks文件的剧情文本，
    并传给ex_ks处理
    """
    ks_path=Path(file_path)
    if not ks_path.exists() or not ks_path.is_dir():
        print("文件夹路径错误，已退出\n")
        return {}
    all_ks_ex_data={}
    ks_file_data=list(ks_path.rglob('*.ks'))
    print(f"扫描完成，共发现{len(ks_file_data)}个ks文件\n")
    for ks_file in ks_file_data:
        ks_file_path=str(ks_file)
        try:
            print(f"尝试提取{ks_file.name}\n")
            ks_file_ex_data=ex_ks(ks_file_path)
            if ks_file_ex_data:
                all_ks_ex_data[ks_file_path]=ks_file_ex_data
        except Exception as e:
            print(f"读取文件{ks_file.name}时出现了问题，将会跳过\n报错信息:{e}")
    return all_ks_ex_data

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
    
def worker_task(batched_task,global_ks_data):
    """
    单线程主逻辑
    单次调用llm并存入总进程字典
    """
    llm_input=SEPARATOR.join(block["block_content"] for block in batched_task)
    for tryed in range(MAX_RETRYS):
        llm_output=call_llm(llm_input)
        if not llm_output:
            continue
        llm_output_blocks=llm_output.split(SEPARATOR)
        tqdm.write(f"翻译结果:\n{"="*40}\n")
        for block in llm_output_blocks:
            tqdm.write(f"{block}\n")
        tqdm.write(f"{"="*40}\n")
        if len(llm_output_blocks)!=len(batched_task):
            tqdm.write(f"文本块数不正确，重试……({tryed}/{MAX_RETRYS})\n")
            continue
        line_mismatch=False
        for block_pos,output_block in enumerate(llm_output_blocks):
            if batched_task[block_pos]["used_line"]!=(output_block.strip().count('\n')+1):
                tqdm.write(f"文本块内部行数不匹配，重试……({tryed}/{MAX_RETRYS})\n")
                line_mismatch=True
                break
        if line_mismatch:
            continue
        with save_lock:
            for block_pos,block in enumerate(llm_output_blocks):
                final_block_content=unmask_text(block.rstrip('\n'),batched_task[block_pos]["tag_list"])
                global_ks_data[batched_task[block_pos]["file_path"]][batched_task[block_pos]["block_pos"]]["translated_block"]=final_block_content
            temp_json=f"{PROGRESS_FILE}.temp_{uuid.uuid4().hex}"
            try:
                with open(temp_json,"w",encoding="utf-8") as f:
                    json.dump(global_ks_data,f,ensure_ascii=False,indent=4)
                os.replace(temp_json,PROGRESS_FILE)
            except Exception as e:
                tqdm.write(f"线程写入错误，可能是并发数过高，错误信息:{e}\n")
                if os.path.exists(temp_json):
                    os.remove(temp_json)
                tqdm.write("3秒后退出程序……")
                time.sleep(3)
                sys.exit(0)
        tqdm.write(f"成功翻译{len(batched_task)}块\n")
        return
    tqdm.write(F"尝试{MAX_RETRYS}次后失败……\n")

def build_output_ks_file(global_ks_data,input_path,output_path):
    """
    检查是否翻译完整，然后将翻译结果替换原文本并另存为新文件
    """
    out_path=Path(output_path)
    out_path.mkdir(parents=True,exist_ok=True)
    replace_count=0
    for file_path,blocks in global_ks_data.items():
        untranslated=[block for block in blocks if not block.get("translated_block")]
        if len(untranslated)>0:
            print(f"文件{Path(file_path).name}未通过完全翻译检查，共{len(untranslated)}个文本块未翻译\n位于:")
            for untranslated_block in untranslated:
                print(f"文件第{untranslated_block['start_line']}行开始,第{untranslated_block['end_line']}结束\n")
            print("已跳过此文件的生成，请手动检查\n")
            continue
        with open(file_path,"rb") as f:
            raw_byte=f.read()
        readed_encoding=None
        for enc in ['utf-16le','utf-8','shiftjis']:
            try:
                text_content=raw_byte.decode(enc)
                readed_encoding=enc
                break
            except UnicodeDecodeError as e:
                continue
        if readed_encoding is None:
            print(f"读取源文件{Path(file_path).name}时解码失败，已跳过\n")
            continue
        lines=text_content.splitlines()
        sorted_blocks=sorted(blocks,key=lambda x:x["start_line"],reverse=True)
        for block in sorted_blocks:
            lines[block["start_line"]:block["end_line"]+1]=block["translated_block"].split('\n')
        fix_path=out_path/Path(file_path).relative_to(Path(input_path))
        fix_path.parent.mkdir(parents=True,exist_ok=True)
        with open(fix_path,'w',encoding='utf-16') as f:
            f.write('\n'.join(lines))
        replace_count+=1
    print(f"已翻译ks文件已保存至路径:{output_path}，共{replace_count}个文件\n")

def start_translation_job():
    global_ks_data={}
    if os.path.exists(PROGRESS_FILE):
        print("目录下存在项目进度，读取中……\n")
        with open(PROGRESS_FILE,"r",encoding="utf-8") as f:
            global_ks_data=json.load(f)
            print("读取项目进度完成\n")
    else:
        print("未发现项目进度，开始扫描……\n")
        global_ks_data=scan_all_ks_file(INPUT_PATH)
        print("提取完成\n")
        with open(PROGRESS_FILE,"w",encoding="utf-8") as f:
            json.dump(global_ks_data,f,ensure_ascii=False,indent=4)
            print(f"已写入项目进度为{PROGRESS_FILE}\n")
    pending_task_data=[]
    for file_path,blocks in global_ks_data.items():
        for block_pos,block_content in enumerate(blocks):
            if not block_content.get("translated_block"):
                pending_task_data.append({"file_path":file_path,"block_pos":block_pos,"block_content":block_content["block_content"],"tag_list":block_content["tag_list"],"used_line":(block_content["end_line"]-block_content["start_line"]+1)})
    batched_tasks=[pending_task_data[i:i+BATCH_SIZE] for i in range(0,len(pending_task_data),BATCH_SIZE)]
    is_complete=False
    if batched_tasks:
        print(f"已将所有未翻译文本块分组完成，按照设置的单次块数:{BATCH_SIZE}进行分组\n共分:{len(batched_tasks)}组\n")
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as threads:
            futures=[threads.submit(worker_task,batched_task,global_ks_data) for batched_task in batched_tasks]
            with tqdm(total=len(futures),desc="总翻译进度",unit="组") as pbar:
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        tqdm.write(f"并发线程崩溃，错误信息:{e}\n")
                    finally:
                        pbar.update(1)
        is_complete=True
    else:
        is_complete=True
    if is_complete:
        print("全部翻译任务已完成\n")
        build_output_ks_file(global_ks_data,INPUT_PATH,OUTPUT_PATH)

def backup_json_data():
    if os.path.exists(PROGRESS_FILE):
        backup_path=Path(BACKUP_PATH)
        backup_path.mkdir(exist_ok=True)
        time_now=datetime.now().strftime("%Y%m%d_%H%M%S")
        json_name,json_ext=os.path.splitext(PROGRESS_FILE)
        backup_json_name=f"{json_name}_{time_now}{json_ext}"
        shutil.copy2(PROGRESS_FILE,backup_path/backup_json_name)
        print(f"旧进度json已备份至{backup_path/backup_json_name}\n")

def update_json_data():
    """
    扫描指定路径下所有文件并比对更新新旧数据
    如果有变动，进行更新
    """
    backup_json_data()
    time.sleep(1.5)
    new_global_ks_data=scan_all_ks_file(INPUT_PATH)
    print(f"提取更新文件完成……\n")
    old_global_ks_data={}
    update_block_count=0
    if os.path.exists(PROGRESS_FILE):
        print("存在旧进度文件，即将进行比对更新……\n")
        with open(PROGRESS_FILE,'r',encoding="utf-8") as f:
            old_global_ks_data=json.load(f)
        for file_path,new_blocks in new_global_ks_data.items():
            old_blocks=old_global_ks_data.get(file_path,[])
            old_translated_to_new={old_block["block_content"]:old_block["translated_block"] for old_block in old_blocks if old_block.get("translated_block")}
            for new_block in new_blocks:
                if new_block["block_content"] in old_translated_to_new:
                    new_block["translated_block"]=old_translated_to_new[new_block["block_content"]]
                    update_block_count+=1
    with open(PROGRESS_FILE,'w',encoding='utf-8') as f:
        json.dump(new_global_ks_data,f,ensure_ascii=False,indent=4)
        print(f"更新路径文件完成，已保存项目进度至{PROGRESS_FILE}\n")
    compare_file_count=len(new_global_ks_data)-len(old_global_ks_data)
    if compare_file_count>0:
        print(f"共新增{compare_file_count}个ks文件\n")
    elif compare_file_count<0:
        print(f"共减少{-compare_file_count}个ks文件\n")
    else:
        print(f"文件数量未变化\n")
    print(f"已有{update_block_count}个已翻译文本块更新至新进度\n")
    return new_global_ks_data

def main_menu():
    while True:
        clear_panel()
        print(f"根据你的目的进行选择:\n")
        print("[0] 退出程序\n")
        print("[1] 更新扫描路径——>有文件变动或更改时选选择此项\n")
        print("[2] 开始翻译任务——>进行全新开始或继续上次的进度\n")
        print("[3] 查看当前配置——>LLM参数,并发数,重试次数\n")
        print("[4] 初始化配置文件\n")
        print()
        print("直接输入数字0~4:",end="",flush=True)
        choice=catch_keyboard(['0','1','2','3','4'])
        if choice=='1':
            clear_panel()
            update_json_data()
            press_to_continue()
        elif choice=='2':
            clear_panel()
            start_translation_job()
            press_to_continue()
        elif choice=='3':
            clear_panel()
            print_information()
            press_to_continue()
        elif choice=='4':
            clear_panel()
            write_default_config()
            press_to_continue()
        elif choice=='0':
            break
        else:
            continue

if __name__ == "__main__":
    
    print_banner()
    main_menu()