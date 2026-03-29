import utils
import llm_api
import config
import json_handle
import ks_extractor

def main_menu(CONFIG):
    """
    主菜单
    等待配置文件读取结束后循环运行的function
    """
    while True:
        utils.clear_panel()
        print(f"根据你的目的进行选择:\n")
        print("[0] 退出程序\n")
        print("[1] 更新扫描路径——>有文件变动或更改时选选择此项\n")
        print("[2] 开始翻译任务——>进行全新开始或继续上次的进度\n")
        print("[3] 查看当前配置——>LLM参数,并发数,重试次数\n")
        print("[4] 初始化配置文件\n")
        print("直接输入数字0~4:",end="",flush=True)
        choice=utils.catch_keyboard(['0','1','2','3','4'])
        if choice=='1':
            utils.clear_panel()
            json_handle.update_json_data()
            utils.press_to_continue()
        elif choice=='2':
            utils.clear_panel()
            ks_extractor.start_translation_job()
            utils.press_to_continue()
        elif choice=='3':
            utils.clear_panel()
            config.print_information(CONFIG)
            utils.press_to_continue()
        elif choice=='4':
            utils.clear_panel()
            config.write_default_config()
            utils.press_to_continue()
        elif choice=='0':
            break
        else:
            continue

def startup():
    """
    初始化配置文件给各种function使用
    并返回读取的配置文件
    """
    CONFIG=config.get_config()
    ks_extractor.init_ks_extractor(CONFIG)
    json_handle.init_json_backup(CONFIG)
    llm_api.init_llm(CONFIG)
    return CONFIG

if __name__ == "__main__":
    CONFIG=startup()
    config.print_banner(CONFIG)
    main_menu(CONFIG)