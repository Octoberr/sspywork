"""
一件生成扫描任务
端口，ip段
记录保存端口模板
保存查询分发记录
"""
import json
import time
import uuid
from datetime import datetime
from pathlib import Path

from .config import file_folder
from .storetask import StoreTask


class GenerateScanTask(object):

    def __init__(self) -> None:
        # super().__init__()
        self.db_name = file_folder / 'generatetask.db'
        self.store_task = StoreTask()

    def process_cmd_dict(self, cmd_dict: dict):
        """
        处理cmd dict
        端口，ip段，地区等
        """
        cmd = {}
        stratagyscan = {}
        scan = {}
        ports = cmd_dict.get('ports')
        scan['ports'] = ports
        hosts = cmd_dict.get('hosts')
        scan['hosts'] = hosts
        location = cmd_dict.get('location')
        scan['location'] = location
        stratagyscan['scan'] = scan
        cmd['stratagyscan'] = stratagyscan
        cmd_str = json.dumps(cmd)
        return cmd_str

    def output_task(self, task_dict: dict):
        """
        输出自己构建好的任务
        """
        # 先创建一个当前时间的文件夹
        now_time = int(time.time())
        now_time_folder = Path(f'./{now_time}')
        now_time_folder.mkdir(exist_ok=True)
        # 然后创建一个任务文件输出即可
        task_file = now_time_folder/f'{int(uuid.uuid1())}.iscan_task'
        lines = ''
        for k, v in task_dict.items():
            lines += f'{k}:{v}\n'
        task_file.write_text(lines.strip(), encoding='utf-8')
        return

    def generate_task(self, input_info: dict, clientid):
        """
        生成任务文件，根据传入的任务信息生成任务文件
        """
        task = {}
        taskid = input_info.get('taskid')
        if taskid is None:
            taskid = str(uuid.uuid1())
        task['taskid'] = taskid
        task['platform'] = 'zplus'
        createtime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task['createtime'] = createtime
        task['source'] = 'asset_repository'
        task['scantype'] = 2
        cmdid = input_info.get('cmdid')
        if cmdid is None:
            cmdid = str(uuid.uuid1())
        task['cmdid'] = cmdid
        cmd_dict = input_info.get('cmd')
        # 处理任务带着的cmd
        task['cmd'] = self.process_cmd_dict(cmd_dict)
        # 输出任务文件
        self.output_task(task)
        # 保存任务文件
        self.store_task.insert_tinfo(json.dumps(input_info), clientid)
        return

    def show_task(self):
        """
        展示已保存的模板
        """
        res = self.store_task.show_me_info()
        return res
