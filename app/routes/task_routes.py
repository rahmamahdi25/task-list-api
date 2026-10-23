from flask import Blueprint, Response, abort, make_response, request

from ..db import db
from ..models.task import Task


tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")


def get_task_by_id(task_id):
    try:
        task_id = int(task_id)
    except (TypeError, ValueError):
        abort(make_response(
            {"message": f"Task id {task_id} invalid"}, 400
        ))

    query = db.select(Task).where(Task.id == task_id)
    task = db.session.scalar(query)

    if task is None:
        abort(make_response(
            {"message": f"Task id {task_id} not found"}, 404
        ))

    return task


def create_instance_from_dict(data, factory):
    try:
        instance = factory(data)
    except (KeyError, ValueError):
        abort(make_response({"details": "Invalid data"}, 400))

    db.session.add(instance)
    db.session.commit()

    return instance, 201


def parse_json_object():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        abort(make_response({"details": "Invalid data"}, 400))

    return data


@tasks_bp.post("")
def create_task():
    data = parse_json_object()
    task, status = create_instance_from_dict(data, Task.from_dict)

    return task.to_dict(), status


@tasks_bp.get("")
def get_all_tasks():
    query = db.select(Task)

    sort_param = request.args.get("sort")

    if sort_param == "asc":
        query = query.order_by(Task.title.asc())
    elif sort_param == "desc":
        query = query.order_by(Task.title.desc())
    else:
        query = query.order_by(Task.id)

    tasks = db.session.scalars(query).all()

    return [task.to_dict() for task in tasks], 200


@tasks_bp.get("/<task_id>")
def get_one_task(task_id):
    task = get_task_by_id(task_id)

    return task.to_dict(), 200


@tasks_bp.put("/<task_id>")
def update_task(task_id):
    task = get_task_by_id(task_id)
    data = parse_json_object()

    try:
        task.title = data["title"]
        task.description = data["description"]
    except KeyError:
        abort(make_response({"details": "Invalid data"}, 400))

    db.session.commit()

    return Response(status=204, mimetype="application/json")


@tasks_bp.delete("/<task_id>")
def delete_task(task_id):
    task = get_task_by_id(task_id)

    db.session.delete(task)
    db.session.commit()

    return Response(status=204, mimetype="application/json")
