import os
import time
import json
from datetime import datetime
from pathlib import Path
import shutil
import ks_extractor

PROGRESS_FILE=""
BACKUP_PATH=""
INPUT_PATH=""

def init_json_backup(CONFIG):
    """
    初始化关于json进度文件相关函数的配置读取
    """
    global PROGRESS_FILE
    global BACKUP_PATH
    global INPUT_PATH
    PROGRESS_FILE=CONFIG["PROGRESS_FILE"]
    BACKUP_PATH=CONFIG["BACKUP_PATH"]
    INPUT_PATH=CONFIG["INPUT_PATH"]

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
    new_global_ks_data=ks_extractor.scan_all_ks_file(INPUT_PATH)
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