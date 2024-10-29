import os
import sys
import time
import subprocess
from datetime import datetime, timedelta
from tzlocal import get_localzone
from zoneinfo import ZoneInfo
from dateutil.relativedelta import relativedelta
from app.task_manager.task_manager import TaskManager


class TaskExecutor:
    """A class to manage the execution and following data updates."""
    def __init__(self, task_manager: TaskManager):
        """
        Initializes the TaskExecutor instance. This method retrieves the tasks from the provided TaskManager instance,
        identifies tasks that are scheduled to run within the next five minutes, and then iterates over each of these
        tasks to execute them and update their details.
        :param task_manager: An instance of TaskManager to handle operations.
        """
        self.task_manager = task_manager
        self.tasks_df = self.task_manager.fetch_tasks()
        self.tasks_df['original_index'] = self.tasks_df.index

        five_minutes_ahead = datetime.now(get_localzone()) + timedelta(minutes=5)
        self.executable_tasks = self.tasks_df[self.tasks_df['next_run'] < five_minutes_ahead].sort_values(by='next_run')

        for task in self.executable_tasks.to_dict(orient='records'):
            sleep_time = (task['next_run'] - datetime.now(tz=get_localzone())).total_seconds()
            if sleep_time > 0:
                time.sleep(sleep_time)

            start_time = datetime.now()
            stdout, stderr = self.run_task(task)
            exec_time = round((datetime.now() - start_time).total_seconds(), 3)
            self.update_task(task, stdout, stderr, exec_time)

    def run_task(self, task: dict, retry: bool = False):
        """
        Executes the task via subprocess.
        :param task: A dictionary representing the executed task's data from the tasks DataFrame.
        :param retry: Boolean representing whether this is the second attempt to run.
        :return: A tuple containing the standard output (stdout) and the standard error (stderr) returned by the
        subprocess. If the task succeeds, stderr will be an empty string; if it fails, stdout may contain partial output
        and stderr will contain the error message.
        """
        # Combine project path with entry module
        full_script_path = os.path.join(task['project_path'], task['entry_module'])

        try:
            result = subprocess.run(
                [sys.executable, full_script_path],
                check=True,
                capture_output=True,
                text=True
            )

            return result.stdout, result.stderr

        except subprocess.CalledProcessError as e:
            # Retry once to protect against temporary issues
            if not retry:
                return self.run_task(task, retry=True)

            return e.stdout, e.stderr

    def update_task(self, task: dict, stdout: str, stderr: str, exec_time: float):
        """
        Updates columns to reflect most recent run.
        :param task: A dictionary representing the executed task's data from the tasks DataFrame.
        :param stdout: The output string from the task executed by subprocess.
        :param stderr: The error string from the task executed by subprocess. If there are no errors, this will be an
        empty string.
        :param exec_time: The time taken for the task to run, in seconds.
        """
        def update_next_run():
            """Updates next_run to the next interval, accounting for skips. Protects against delayed runs by iterating
            until the next_run is in the future."""
            while task['next_run'] < datetime.now(tz=get_localzone()):
                schedule_interval = task['schedule_interval'].lower()
                skip_intervals = task['skip_intervals'] + 1
                delta_kwargs = {schedule_interval: skip_intervals}

                if schedule_interval in ['months', 'years']:
                    task['next_run'] += relativedelta(**delta_kwargs)
                elif schedule_interval in ['minutes', 'hours', 'days', 'weeks']:
                    task['next_run'] += timedelta(**delta_kwargs)
                else:
                    raise ValueError(f'Unsupported interval: {schedule_interval}')

        def update_last_run():
            """Updates last_run to the current time as a timezone-aware Unix timestamp in UTC."""
            task['last_run'] = datetime.now(tz=get_localzone()).astimezone(ZoneInfo('UTC')).timestamp()

        def update_run_count():
            """Increments the run count by 1."""
            task['run_count'] += 1

        def update_last_exec_time():
            """Overwrites last_exec_time with the new value."""
            task['last_exec_time'] = exec_time

        def update_avg_exec_time():
            """Calculates the updated avg_run_time."""
            avg_exec = task['avg_exec_time'] or 0
            last_exec = task['last_exec_time']
            run_count = task['run_count']
            task['avg_exec_time'] = round((avg_exec * (run_count - 1) + last_exec) / run_count, 3)

        def update_prev_five_success():
            """Updates the prev_five_success string by inserting the latest success (1 for success, 0 for failure)
            at position 0 and deleting the oldest success at position -1."""
            response = '0' if stderr else '1'
            responses_list = task['prev_five_success'].split('|')
            responses_list.insert(0, response)
            del responses_list[-1]
            task['prev_five_success'] = '|'.join(responses_list)

        def update_last_note():
            """Overwrites last_note with the new value: stderr if there's an error, stdout otherwise."""
            task['last_note'] = stderr or stdout

        update_next_run()
        update_last_run()
        update_run_count()
        update_last_exec_time()
        update_avg_exec_time()
        update_prev_five_success()
        update_last_note()

        self.task_manager.edit_task(task['original_index'], task)
