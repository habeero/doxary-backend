from flask import Blueprint, current_app, jsonify
from pydantic import BaseModel, ConfigDict

from app.analysis.contracts import AnalysisResult
from app.health.api import health_blueprint
from app.operations.application.status import OperationStatusQuery, PublicOperationStatus

api_v1 = Blueprint("api_v1", __name__)
api_v1.register_blueprint(health_blueprint)


class OperationStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation_id: str
    status: PublicOperationStatus
    result: AnalysisResult | None = None
    failure: dict[str, str] | None = None


@api_v1.get("/operations/<operation_id>")
def get_operation_status(operation_id: str):
    container = current_app.extensions["doxary_container"]
    view = OperationStatusQuery(container.session_factory).get(operation_id)
    response = OperationStatusResponse(
        operation_id=view.operation_id,
        status=view.status,
        result=view.result,
        failure={"code": view.failure_code} if view.failure_code else None,
    )
    result = jsonify(response.model_dump(mode="json"))
    result.headers["Cache-Control"] = "private, no-store"
    return result
