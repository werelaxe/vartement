import json
from time import sleep

import requests


CODE = """
f = num(x: num) -> f(add(x, 1))
f(900) = 0
null = print(f(1))
"""

TASK_TEMPLATE = """{{
    "source": "{}",
    "stdin": "{}",
    "token": "my_token"
}}
"""


def add_new_task(source, stdin):
    data = TASK_TEMPLATE.format(source.replace('\n', '\\n'), stdin)
    return requests.post("http://0.0.0.0:8080/run_task", data=data)


def get_info(task_id):
    return requests.get("http://0.0.0.0:8080/info/{}?token=my_token".format(task_id)).content.decode()


def main():
    raw_respn = add_new_task(CODE, "").content.decode()
    res = json.loads(raw_respn)
    task_id = res['task_id']
    for _ in range(5):
        sleep(0.2)
        print(get_info(task_id))


if __name__ == '__main__':
    main()
