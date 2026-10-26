from datetime import datetime

from flask import Blueprint, Response, request

from ..db import db
from ..models.task import Task
from .route_utilities import (
    validate_model,
    parse_json_object,
    send_slack_notification,
    create_model,
    get_models_with_filters,
    update_model,
)


tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")


def get_task_by_id(task_id):
    return validate_model(Task, task_id)


@tasks_bp.post("")
def create_task():
    data = parse_json_object()
    return create_model(Task, data)


@tasks_bp.get("")
def get_all_tasks():
    filters = request.args.to_dict()
    tasks = get_models_with_filters(Task, filters)
    return tasks, 200


@tasks_bp.get("/<task_id>")
def get_one_task(task_id):
    task = get_task_by_id(task_id)

    return task.to_dict(), 200


@tasks_bp.put("/<task_id>")
def update_task(task_id):
    task = get_task_by_id(task_id)
    data = parse_json_object()

    if "title" not in data or "description" not in data:
        from flask import abort, make_response
        abort(make_response({"details": "Invalid data"}, 400))

    return update_model(task, {
        "title": data["title"],
        "description": data["description"]
    })


@tasks_bp.patch("/<task_id>/mark_complete")
def mark_task_complete(task_id):
    task = get_task_by_id(task_id)

    task.completed_at = datetime.now()
    db.session.commit()

    send_slack_notification(
        f"Someone just completed the task {task.title}"
    )

    return Response(status=204, mimetype="application/json")


@tasks_bp.patch("/<task_id>/mark_incomplete")
def mark_task_incomplete(task_id):
    task = get_task_by_id(task_id)

    task.completed_at = None
    db.session.commit()

    return Response(status=204, mimetype="application/json")


@tasks_bp.delete("/<task_id>")
def delete_task(task_id):
    task = get_task_by_id(task_id)

    db.session.delete(task)
    db.session.commit()

    return Response(status=204, mimetype="application/json")
