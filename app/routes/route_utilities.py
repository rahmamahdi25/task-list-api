import logging
import os

import requests
from flask import abort, make_response, request, Response

from ..db import db


logger = logging.getLogger(__name__)


def get_instance_by_id(instance_id, model, model_name=None):
    """Retrieve a model by ID or abort with an appropriate HTTP error."""
    if model_name is None:
        model_name = model.__name__

    try:
        instance_id = int(instance_id)
    except (TypeError, ValueError):
        abort(make_response(
            {"message": f"{model_name} id {instance_id} invalid"},
            400
        ))

    instance = db.session.get(model, instance_id)

    if instance is None:
        abort(make_response(
            {"message": f"{model_name} id {instance_id} not found"},
            404
        ))

    return instance


def validate_model(model, model_id):
    """Validate a model ID and return the matching database instance"""
    return get_instance_by_id(model_id, model)


def parse_json_object():
    """Require the request body to be a JSON object."""
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        abort(make_response({"details": "Invalid data"}, 400))

    return data


def get_models_with_filters(cls, filters=None):
    query = db.select(cls)
    filters = filters or {}

    sort_param = filters.get("sort")
    sort_by = filters.get("sort_by")

    for attribute, value in filters.items():
        if attribute in ("sort", "sort_by"):
            continue

        if hasattr(cls, attribute):
            query = query.where(getattr(cls, attribute) == value)

    if sort_by and hasattr(cls, sort_by):
        sort_column = getattr(cls, sort_by)

        if sort_param == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

    elif sort_param == "asc":
        query = query.order_by(cls.title.asc())
    elif sort_param == "desc":
        query = query.order_by(cls.title.desc())
    elif hasattr(cls, "id"):
        query = query.order_by(cls.id)

    models = db.session.scalars(query).all()

    return [model.to_dict() for model in models]


def create_model(model, request_body):
    """Create a model instance and return its serialized data and status."""
    try:
        instance = model.from_dict(request_body)
    except (KeyError, ValueError, TypeError):
        abort(make_response({"details": "Invalid data"}, 400))

    db.session.add(instance)
    db.session.commit()

    return instance.to_dict(), 201


def send_slack_notification(message):
    """Send a Slack notification and log delivery failures."""
    token = os.environ.get("SLACK_BOT_TOKEN")
    channel = os.environ.get("SLACK_CHANNEL", "task-notifications")

    if not token:
        logger.warning(
            "Slack notification skipped: SLACK_BOT_TOKEN is not configured"
        )
        return

    try:
        response = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {token}"},
            json={"channel": channel, "text": message}
        )

        response.raise_for_status()
        result = response.json()

        if not result.get("ok"):
            logger.warning(
                "Slack notification failed: %s",
                result.get("error", "Unknown Slack API error")
            )

    except (requests.RequestException, ValueError):
        logger.exception("Failed to send Slack notification")


def update_model(obj, data):
    for attr, value in data.items():
        if hasattr(obj, attr):
            setattr(obj, attr, value)
    
    db.session.commit()

    return Response(status=204, mimetype='application/json')
