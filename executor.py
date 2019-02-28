import os
from collections import namedtuple
from enum import Enum
from subprocess import check_output
from concurrent.futures import ProcessPoolExecutor, Future
from random import randint
from time import sleep

from lang.translate import translate, ParsingError, TranslationError

TASKS_PATH = "tasks"


def execute_task(task_id, task_source, stdin):
    bin_filename = os.path.join(TASKS_PATH, task_id)
    cpp_filename = bin_filename + ".cpp"
    with open(cpp_filename, "w") as file:
        file.write(translate(task_source, stdin))
    check_output(["g++", cpp_filename, "-o", bin_filename])
    return check_output([bin_filename]).decode()


class TaskStatus(Enum):
    RUNNING = 0
    DONE = 1
    ERROR = 2


TaskInfo = namedtuple("TaskInfo", ["status", "stdout", "error"])


class VtaExecutor:
    def __init__(self):
        self._executor = ProcessPoolExecutor(max_workers=256)
        self.tasks = {}
        self.task_count = 0

    def execute_task(self, task_source, stdin):
        task_id = str(self.task_count)
        self.task_count += 1
        self.tasks[task_id] = self._executor.submit(execute_task, task_id, task_source, stdin)
        # execute_task(task_id, task_source, stdin)
        return task_id

    def task_info(self, task_id):
        if self.tasks[task_id].running():
            return TaskInfo(TaskStatus.RUNNING, "", "")
        elif self.tasks[task_id].done():
            try:
                print(TaskStatus.DONE, self.tasks[task_id].result(0), "")
                result = TaskInfo(TaskStatus.DONE, self.tasks[task_id].result(0), "")
                return result
            except (ParsingError, TranslationError) as e:
                print(e)
                print(type(e))
                print(str(e))
                return TaskInfo(TaskStatus.ERROR, "", str(e))
        raise Exception("Kek?")
