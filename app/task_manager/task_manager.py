import os
import subprocess
import logging
from typing import Union, Dict
from tzlocal import get_localzone
import pandas as pd
from app.task_executor.task_scheduler import schedule_task

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskManager:
    """A class to manage tasks, including loading from and saving to a CSV file."""
    COLUMNS = ['project_name', 'project_path', 'entry_module', 'next_run', 'schedule_interval', 'skip_intervals',
               'status_change_date', 'notify_on_run', 'date_created', 'status', 'last_run', 'run_count',
               'last_exec_time', 'avg_exec_time', 'prev_five_success', 'last_note']

    def __init__(self):
        """Initializes the task manager by loading tasks from a CSV file."""
        self.data_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'tasks_data.csv')
        self.run_scheduled = None
        self.check_schedule()
        self.tasks_df = None
        self.load_tasks()

    def load_tasks(self):
        """Loads tasks from the CSV file. If the file does not exist, creates a new DataFrame with default columns."""
        try:
            self.tasks_df = pd.read_csv(self.data_file_path).fillna('')
            logger.info(f'Loaded tasks from {self.data_file_path}.')

        except FileNotFoundError:
            logger.info(f'Tasks file not found at {self.data_file_path}. Creating a new tasks DataFrame.')
            self.tasks_df = pd.DataFrame(columns=self.COLUMNS)
            self.save_tasks()

    def save_tasks(self):
        """Saves the current DataFrame to the CSV file."""
        for col in ['next_run', 'status_change_date', 'date_created', 'last_run']:
            self.tasks_df[col] = self.tasks_df[col].apply(
                lambda x: x.timestamp() if isinstance(x, pd.Timestamp) else x if isinstance(x, float) else ''
            )

        self.tasks_df.to_csv(self.data_file_path, index=False)

        if not self.run_scheduled and len(self.tasks_df) > 0:
            self.schedule_run()

    def fetch_tasks(self) -> pd.DataFrame:
        """
        Retrieves the current tasks DataFrame. Converts floats to timestamps and localizes to local timezone.
        :return: A pandas DataFrame containing the tasks.
        """
        for col in ['next_run', 'status_change_date', 'date_created', 'last_run']:
            self.tasks_df[col] = pd.to_datetime(self.tasks_df[col], unit='s', errors='coerce', utc=True)
            self.tasks_df[col] = self.tasks_df[col].dt.tz_convert(get_localzone())

        return self.tasks_df

    def add_task(self, new_task: Dict[str, Union[str, int, float, pd.Timestamp]]):
        """
        Adds a new task to the DataFrame.
        :param new_task: A dictionary containing task details.
        """
        filtered_task = {key: new_task[key] for key in self.COLUMNS}
        new_row_df = pd.DataFrame([filtered_task])

        for col in ['next_run', 'status_change_date', 'date_created', 'last_run']:
            if col in new_task and isinstance(new_task[col], pd.Timestamp):
                new_task[col] = new_task[col].timestamp()

        self.tasks_df = pd.concat([self.tasks_df, new_row_df], ignore_index=True)
        self.save_tasks()
        logger.info(f'Added new task: {new_task['project_name']}')

    def toggle_status(self, index: int):
        """
        Toggles a specified status in the DataFrame between Active and Paused.
        :param index: The index of the tasks to toggle.
        """
        if self.tasks_df.at[index, 'status'] == 'Active':
            self.tasks_df.at[index, 'status'] = 'Paused'
            logger.info(f'Set status for {self.tasks_df.at[index, 'project_name']} to "Paused"')
        else:
            self.tasks_df.at[index, 'status'] = 'Active'
            logger.info(f'Set status for {self.tasks_df.at[index, 'project_name']} to "Active"')
        self.save_tasks()

    def toggle_notify(self, index: int):
        """
        Toggles a specified notify_on_run in the DataFrame between 0 and 1.
        :param index: The index of the tasks to toggle.
        """
        if self.tasks_df.at[index, 'notify_on_run'] == 0:
            self.tasks_df.at[index, 'notify_on_run'] = 1
            logger.info(f'Turned on notifications for {self.tasks_df.at[index, 'project_name']}')
        else:
            self.tasks_df.at[index, 'notify_on_run'] = 0
            logger.info(f'Turned off notifications for {self.tasks_df.at[index, 'project_name']}')
        self.save_tasks()

    def edit_task(self, index: int, updated_task: Dict[str, Union[str, int, float, pd.Timestamp]]):
        """
        Edits an existing task in the DataFrame.
        :param index: The index of the task to update.
        :param updated_task: The new value to set.
        """
        filtered_task = {key: updated_task[key] for key in self.COLUMNS}
        project_name = filtered_task['project_name']
        self.tasks_df.loc[index] = filtered_task
        self.save_tasks()
        logger.info(f'Edited task: {project_name}')

    def delete_task(self, index: int):
        """
        Deletes a task from the DataFrame.
        :param index: The index of the task to delete.
        """
        project_name = self.tasks_df.at[index, 'project_name']
        self.tasks_df.drop(index=index, inplace=True)
        self.tasks_df.reset_index(drop=True, inplace=True)
        self.save_tasks()
        logger.info(f'Deleted task {project_name}.')

    def view_task(self, index: int):
        """
        Opens the task in a new PyCharm window.
        :param index: The index of the task to view.
        """
        pycharm_executable = '/Applications/PyCharm CE.app/Contents/MacOS/pycharm'
        project_path = self.tasks_df.at[index, 'project_path']
        subprocess.run([pycharm_executable, project_path])

    def check_schedule(self):
        self.run_scheduled = os.path.exists(os.path.expanduser('~/Library/LaunchAgents/com.life_manager.execute.plist'))

    def schedule_run(self):
        schedule_task(self.fetch_tasks()['next_run'].min())
        self.check_schedule()

