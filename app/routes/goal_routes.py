from flask import Blueprint, Response, abort, make_response

from ..db import db
from ..models.goal import Goal
from ..models.task import Task
from .route_utilities import (
    get_instance_by_id,
    parse_json_object,
    validate_model,
    create_model,

)

goals_bp = Blueprint("goals", __name__, url_prefix="/goals")


def get_goal_by_id(goal_id):
    """Retrieve a goal by ID, allows a custom model name for error messages."""
    return get_instance_by_id(goal_id, Goal, "Goal")


@goals_bp.post("")
def create_goal():
    data = parse_json_object()
    return create_model(Goal, data)
    

@goals_bp.post("/<goal_id>/tasks")
def add_tasks_to_goal(goal_id):
    goal = get_goal_by_id(goal_id)
    data = parse_json_object()
    task_ids = data.get("task_ids")

    if not isinstance(task_ids, list):
        abort(make_response({"details": "Invalid data"}, 400))

    tasks = []

    for task_id in task_ids:
        
        task = validate_model(Task, task_id)
        tasks.append(task)

    goal.tasks = tasks
    db.session.commit()

    return {
        "id": goal.id,
        "task_ids": [task.id for task in goal.tasks]
    }, 200


@goals_bp.get("/<goal_id>/tasks")
def get_tasks_for_goal(goal_id):
    goal = get_goal_by_id(goal_id)

    return {
        "id": goal.id,
        "title": goal.title,
        "tasks": [task.to_dict() for task in goal.tasks]
    }, 200


@goals_bp.get("")
def get_all_goals():
    query = db.select(Goal).order_by(Goal.id)
    goals = db.session.scalars(query).all()

    return [goal.to_dict() for goal in goals], 200


@goals_bp.get("/<goal_id>")
def get_one_goal(goal_id):
    goal = get_goal_by_id(goal_id)

    return goal.to_dict(), 200


@goals_bp.put("/<goal_id>")
def update_goal(goal_id):
    goal = get_goal_by_id(goal_id)
    data = parse_json_object()

    try:
        goal.title = data["title"]
    except KeyError:
        abort(make_response({"details": "Invalid data"}, 400))

    db.session.commit()

    return Response(status=204, mimetype="application/json")


@goals_bp.delete("/<goal_id>")
def delete_goal(goal_id):
    goal = get_goal_by_id(goal_id)

    db.session.delete(goal)
    db.session.commit()

    return Response(status=204, mimetype="application/json")
