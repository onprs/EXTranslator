import os
import re
import sys
import uuid
import json
import time
#import charset_normalizer
import llm_api
import threading
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor,as_completed

save_lock=threading.Lock()

INPUT_PATH=""
OUTPUT_PATH=""
PROGRESS_FILE=""
BATCH_SIZE=0
MAX_THREADS=0
MAX_RETRYS=0
SEPARATOR=""

def init_ks_extractor(CONFIG):
    """
    初始化ks文件读取的配置内容
    """
    global INPUT_PATH,OUTPUT_PATH,PROGRESS_FILE,BATCH_SIZE,MAX_THREADS,MAX_RETRYS,SEPARATOR
    INPUT_PATH=CONFIG["INPUT_PATH"]
    OUTPUT_PATH=CONFIG["OUTPUT_PATH"]
    PROGRESS_FILE=CONFIG["PROGRESS_FILE"]
    BATCH_SIZE=CONFIG["BATCH_SIZE"]
    MAX_THREADS=CONFIG["MAX_THREADS"]
    MAX_RETRYS=CONFIG["MAX_RETRYS"]
    SEPARATOR=CONFIG["SEPARATOR"]

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
    用循环的方式进行编码试探
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
        abs_ks_file_path=str(ks_file)
        rel_ks_file_path=str(ks_file.relative_to(ks_path)).replace('\\','/')
        try:
            print(f"尝试提取{ks_file.name}\n")
            ks_file_ex_data=ex_ks(abs_ks_file_path)
            if ks_file_ex_data:
                all_ks_ex_data[rel_ks_file_path]=ks_file_ex_data
        except Exception as e:
            print(f"读取文件{ks_file.name}时出现了问题，将会跳过\n报错信息:{e}")
    return all_ks_ex_data
    
def worker_task(batched_task,global_ks_data):
    """
    单线程主逻辑
    单次调用llm并存入总进程字典
    """
    llm_input=SEPARATOR.join(block["block_content"] for block in batched_task)
    for tryed in range(MAX_RETRYS):
        llm_output=llm_api.call_llm(llm_input)
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
    in_path=Path(input_path)
    out_path.mkdir(parents=True,exist_ok=True)
    replace_count=0
    for file_path,blocks in global_ks_data.items():
        untranslated=[block for block in blocks if not block.get("translated_block")]
        if len(untranslated)>0:
            print(f"文件{file_path}未通过完全翻译检查，共{len(untranslated)}个文本块未翻译\n位于:")
            for untranslated_block in untranslated:
                print(f"文件第{untranslated_block['start_line']}行开始,第{untranslated_block['end_line']}结束\n")
            print("已跳过此文件的生成，请手动检查\n")
            continue
        with open(in_path/file_path,"rb") as f:
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
        fix_path=out_path/file_path
        fix_path.parent.mkdir(parents=True,exist_ok=True)
        with open(fix_path,'w',encoding='utf-16') as f:
            f.write('\n'.join(lines))
        replace_count+=1
    print(f"已翻译ks文件已保存至路径:{output_path}，共{replace_count}个文件\n")

def start_translation_job():
    """
    开始多线程翻译任务的主函数
    """
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
