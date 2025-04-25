from fastapi import APIRouter, HTTPException, status
from app.celery.celery_app import celery_app
from app.schemas.task import TaskStatus
from celery.result import AsyncResult

router = APIRouter()

@router.get("/{task_id}", response_model=TaskStatus)
def get_task_status_endpoint(task_id: str):
    """
    Consulta el estado y el resultado de una tarea Celery por su ID.
    """
    task_result = AsyncResult(task_id, app=celery_app)

    result_data = None
    if task_result.ready():
        if task_result.successful():
            result_data = task_result.get()
        else:
            try:
                task_result.get()
            except Exception as e:
                result_data = {"error": type(e).__name__, "message": str(e)}
            if not result_data and task_result.info:
                 result_data = task_result.info

    if task_result.state == 'FAILURE' and not result_data:
        result_data = {"error": "Unknown", "message": "La tarea falló sin detalles adicionales."}

    return TaskStatus(
        task_id=task_id,
        status=task_result.state,
        result=result_data
    )