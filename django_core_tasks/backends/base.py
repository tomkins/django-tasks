from typing import ParamSpec, TypeVar

from asgiref.sync import sync_to_async
from django.utils import timezone

from django_core_tasks.exceptions import InvalidTaskError
from django_core_tasks.task import Task, TaskResult
from django_core_tasks.utils import is_global_function

T = TypeVar("T")
P = ParamSpec("P")


class BaseTaskBackend:
    task_class = Task

    supports_defer = False

    def __init__(self, options: dict) -> None:
        self.alias = options["ALIAS"]

    def validate_task(self, task: Task) -> None:
        """
        Determine whether the provided task is one which can be executed by the backend.
        """
        if not is_global_function(task.func):
            raise InvalidTaskError(
                "Task function must be a globally importable function"
            )

        if task.priority is not None and task.priority < 1:
            raise InvalidTaskError("priority must be positive")

        if not self.supports_defer and task.run_after is not None:
            raise InvalidTaskError("Backend does not support run_after")

        if task.run_after is not None and not timezone.is_aware(task.run_after):
            raise InvalidTaskError("run_after must be an aware datetime")

    def enqueue(
        self, task: Task[P, T], args: P.args, kwargs: P.kwargs
    ) -> TaskResult[T]:
        """
        Queue up a task to be executed
        """
        raise NotImplementedError()  # pragma: no cover

    async def aenqueue(
        self, task: Task[P, T], args: P.args, kwargs: P.kwargs
    ) -> TaskResult[T]:
        """
        Queue up a task function (or coroutine) to be executed
        """
        return await sync_to_async(self.enqueue, thread_sensitive=True)(
            task=task, args=args, kwargs=kwargs
        )

    def get_result(self, result_id: str) -> TaskResult:
        """
        Retrieve a result by its id (if one exists).
        If one doesn't, raises ResultDoesNotExist.
        """
        raise NotImplementedError("This backend does not support retrieving results.")

    async def aget_result(self, result_id: str) -> TaskResult:
        """
        Queue up a task function (or coroutine) to be executed
        """
        return await sync_to_async(self.get_result, thread_sensitive=True)(
            result_id=result_id
        )

    def close(self) -> None:
        """
        Close any connections opened as part of the constructor
        """
        ...
