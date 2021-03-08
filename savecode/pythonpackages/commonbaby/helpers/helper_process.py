"""help for process"""

# -*- coding:utf-8 -*-

from subprocess import check_output
import os


def get_pid(proc_name: str) -> map:
    """get process_id of given process name, return map[pids]"""
    return map(int, check_output(["pidof", proc_name]).split())


def kill(proc_name: str):
    """kill all process that are of given process name"""
    for pid in get_pid(proc_name):
        os.kill(pid)


def kill_try(proc_name: str) -> list:
    """try to kill all process that are of given process name"""
    killed = []
    for pid in get_pid(proc_name):
        try:
            os.kill(pid)
            killed.append(pid)
        except Exception:
            pass
    return killed
