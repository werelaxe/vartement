import os
from subprocess import check_output
from concurrent.futures import ProcessPoolExecutor
from random import randint
from time import sleep

from lang.translate import translate


TASKS_PATH = "tasks"


def execute_task(task_id, task_source, stdin):
    bin_filename = os.path.join(TASKS_PATH, task_id)
    cpp_filename = bin_filename + ".cpp"
    with open(cpp_filename, "w") as file:
        file.write(translate(task_source, stdin))
    print(check_output(["g++", cpp_filename, "-o", bin_filename]))
    print(check_output([bin_filename]))
    return "Yes!"


class VtaExecutor:
    def __init__(self):
        self._executor = ProcessPoolExecutor(max_workers=256)
        self.tasks = {}

    def execute_task(self, task_source, stdin):
        task_id = str(randint(10 ** 4, 10 ** 5 - 1))
        self.tasks[task_id] = self._executor.submit(execute_task, task_id, task_source, stdin)
        # execute_task(task_id, task_source, stdin)
        return task_id

    def get_task_status(self, task_id):
        print(self.tasks[task_id])
        print(dir(self.tasks[task_id]))
        return "No!"
