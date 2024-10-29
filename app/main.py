import os
from app.user_interface.home_view import HomeUI
from app.task_manager.task_manager import TaskManager
from app.task_executor.task_executor import TaskExecutor


def main():
    """The main entrypoint for the application."""
    task_manager = TaskManager()

    if 'LAUNCHD_JOB' in os.environ:
        TaskExecutor(task_manager)
    else:
        HomeUI(task_manager)


if __name__ == '__main__':
    main()
