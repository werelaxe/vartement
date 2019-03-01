import io
import json

from bottle import route, run, request, post, get, static_file, redirect, abort, response, jinja2_view as view
import redis

from executor import VtaExecutor, TaskStatus

r = redis.StrictRedis(host='localhost', port=6379, db=0)
vta_executor = VtaExecutor()


@get("/static/<filepath:re:.*>")
def get_static_files(filepath):
    return static_file(filepath, root="static")


@post("/run_task")
def run_task():
    data = json.loads(request.body.read().decode())
    source = data.get('source')
    stdin = data.get('stdin')
    token = data.get('token')

    task_id = vta_executor.execute_task(source, io.StringIO(stdin + "\n"))
    r.set(task_id, token)

    return json.dumps({"task_id": task_id})


@get("/info/<task_id>")
def info(task_id):
    expected_token = r.get(task_id).decode()
    real_token = request.GET.get("token")
    if expected_token != real_token:
        abort(403)

    info = vta_executor.task_info(task_id)
    if info.status == TaskStatus.DONE:
        return json.dumps({
            "task_status": "done",
            "stdout": info.stdout,
        })
    elif info.status == TaskStatus.RUNNING:
        return json.dumps({
            "task_status": "running",
        })
    else:
        return json.dumps({
            "task_status": "error",
            "error": info.error,
        })


def main():
    run(host="0.0.0.0", port=8080)


if __name__ == '__main__':
    main()
