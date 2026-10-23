from flask import Blueprint, Response, abort, make_response, request

from ..db import db
from ..models.goal import Goal


goals_bp = Blueprint("goals", __name__, url_prefix="/goals")


def get_goal_by_id(goal_id):
    try:
        goal_id = int(goal_id)
    except (TypeError, ValueError):
        abort(make_response(
            {"message": f"Goal id {goal_id} invalid"}, 400
        ))

    query = db.select(Goal).where(Goal.id == goal_id)
    goal = db.session.scalar(query)

    if goal is None:
        abort(make_response(
            {"message": f"Goal id {goal_id} not found"}, 404
        ))

    return goal


def parse_json_object():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        abort(make_response({"details": "Invalid data"}, 400))

    return data


@goals_bp.post("")
def create_goal():
    data = parse_json_object()

    try:
        goal = Goal.from_dict(data)
    except (KeyError, ValueError):
        abort(make_response({"details": "Invalid data"}, 400))

    db.session.add(goal)
    db.session.commit()

    return goal.to_dict(), 201


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
