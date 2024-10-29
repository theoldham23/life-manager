from pathlib import Path
import importlib.util
from datetime import datetime, timedelta
from tkinter import messagebox

import pandas as pd
from tzlocal import get_localzone
from zoneinfo import ZoneInfo
from app.task_manager.task_manager import TaskManager


class TaskFormManager:
    """Handles operations for the Task Form"""
    TOMORROW = (datetime.now() + timedelta(days=1)).strftime('%m/%d/%Y')
    LOCAL_TZ = get_localzone()

    def __init__(self, task_manager: TaskManager, edit_index: int = None):
        """
        Initializes the TaskFormManager by unpacking data and setting default values for the fields.
        :param task_manager: An instance of TaskManager to handle operations.
        :param edit_index: Optionally, pass an index for existing task dictionary to automatically populate fields.
        """
        self.task_manager = task_manager
        self.edit_index = edit_index
        self.new_task = edit_index is None

        if not self.new_task:
            self.existing_task = self.load_existing_task()

        # Initiate fields using existing data if editing, defaults if adding
        self.fields = {
            'project_name': '' if self.new_task else self.existing_task['project_name'],
            'project_path': '' if self.new_task else self.existing_task['project_path'],
            'entry_module': '' if self.new_task else self.existing_task['entry_module'],
            'start_date': self.TOMORROW if self.new_task else self.existing_task['start_date'],
            'start_time': '9:00' if self.new_task else self.existing_task['start_time'],
            'am_pm': 'AM' if self.new_task else self.existing_task['am_pm'],
            'schedule_interval': 'Weeks' if self.new_task else self.existing_task['schedule_interval'],
            'skip_intervals': 0 if self.new_task else self.existing_task['skip_intervals'],
            'status_change_date': '' if self.new_task else self.existing_task['status_change_date'],
            'notify_on_run': 1 if self.new_task else self.existing_task['notify_on_run'],
            'date_created': datetime.now().timestamp() if self.new_task else self.existing_task['date_created'],
            'status': 'Active' if self.new_task else self.existing_task['status'],
            'last_run': None if self.new_task else self.existing_task['last_run'],
            'run_count': 0 if self.new_task else self.existing_task['run_count'],
            'last_exec_time': None if self.new_task else self.existing_task['last_exec_time'],
            'avg_exec_time': None if self.new_task else self.existing_task['avg_exec_time'],
            'prev_five_success': '-|-|-|-|-' if self.new_task else self.existing_task['prev_five_success'],
            'last_note': None if self.new_task else self.existing_task['last_note']
        }

    def load_existing_task(self):
        """
        Loads existing task details from the TaskManager for editing.
        :return: A dictionary representing the task to edit to use as the default values.
        """
        task_dict = self.task_manager.fetch_tasks().loc[self.edit_index].to_dict()

        # Split next_run into start_date, start_time and am_pm, convert to strings
        next_run_dt = task_dict['next_run'].to_pydatetime()
        task_dict['start_date'] = next_run_dt.strftime('%m/%d/%Y')
        task_dict['start_time'] = next_run_dt.strftime('%I:%M')
        task_dict['am_pm'] = next_run_dt.strftime('%p')

        # Convert status_change_date to string
        status_change_date_dt = task_dict['status_change_date'].to_pydatetime()
        if pd.isna(status_change_date_dt):
            task_dict['status_change_date'] = ''
        else:
            task_dict['status_change_date'] = status_change_date_dt.strftime('%m/%d/%Y')

        return task_dict

    def validate(self):
        """
        Validates user input from the popup form.
        :return: True if the data is valid; otherwise it displays an error message using a messagebox and returns False.
        """

        def show_error(title: str, message: str):
            """Helper function to format and show errors."""
            messagebox.showerror(title=title, message=message)
            return False

        def mandatory_fields():
            """Ensure all mandatory boxes aren't empty (excluding status_change and notify_on_run)"""
            required_fields = ['project_name', 'project_path', 'entry_module', 'start_date', 'start_time', 'am_pm',
                               'schedule_interval', 'skip_intervals']
            missing_fields = [field for field in required_fields if not self.fields[field]]

            if missing_fields:
                formatted_fields = ', '.join(field.replace('_', ' ').title() for field in missing_fields)
                return show_error('Missing Required Fields', f'Missing required fields: {formatted_fields}')

            return True

        def date_formats():
            """Validate date formats in start_date, status_change"""
            wrong_format_fields = []
            for field in ['start_date', 'status_change_date']:
                if field == 'status_change_date' and not self.fields[field]:
                    continue  # Allow status_change_date to be empty
                try:
                    datetime.strptime(self.fields[field], '%m/%d/%Y')
                except ValueError:
                    wrong_format_fields.append(field)

            if wrong_format_fields:
                formatted_fields = ', '.join(field.replace('_', ' ').title() for field in wrong_format_fields)
                return show_error('Wrong Date Format',
                                  f'Error in {formatted_fields}. Format should be MM/DD/YYYY.'
                                  f'\nExample: {datetime.now().strftime('%m/%d/%Y')}')
            return True

        def time_format():
            """Validate time format in start_time"""
            try:
                datetime.strptime(f'{self.fields['start_time']} {self.fields['am_pm']}', '%I:%M %p')
            except ValueError:
                return show_error('Wrong Time Format', f'Error in Start Time. Format should be as follows:\n'
                                                       f'{datetime.now().strftime('%I:%M %p')}')

            return True

        def set_next_run():
            """Set next_run after start_date, start_time, am_pm are validated"""
            start_strs = [self.fields['start_date'], self.fields['start_time'], self.fields['am_pm']]
            try:
                local_dt = datetime.strptime(' '.join(start_strs), '%m/%d/%Y %I:%M %p')
                self.fields['next_run'] = local_dt.replace(tzinfo=self.LOCAL_TZ)
            except ValueError:
                return show_error('Invalid DateTime', 'Could not combine Start Date and Time into a valid DateTime.')

            return True

        def start_in_future():
            """Validate next_run datetime object is in the future"""
            if self.fields['next_run'] <= datetime.now(tz=self.LOCAL_TZ):
                messagebox.showerror(
                    title='Start Date Error',
                    message='Start Date and Time must be in the future.'
                )
                return show_error('Start Date Error', 'Start Date and Time must be in the future.')

            return True

        def status_change_after_start():
            """Validate status_change_date is after start_date"""
            if not self.fields['status_change_date']:
                return True  # Allow empty

            local_dt = datetime.strptime(
                f'{self.fields['status_change_date']} 11:59 PM',
                '%m/%d/%Y %I:%M %p'
            )
            self.fields['status_change_date'] = local_dt.replace(tzinfo=self.LOCAL_TZ)

            if self.fields['status_change_date'] < self.fields['next_run']:
                return show_error('Status Change Date Before Start Date',
                                  'Status Change Date must be after Start Date.')

            return True

        def skips_is_int():
            """Validate skip_intervals is an integer"""
            try:
                skips_float = float(self.fields['skip_intervals'])
                if not skips_float.is_integer() or skips_float < 0:
                    raise ValueError
                else:
                    self.fields['skip_intervals'] = int(skips_float)
            except ValueError:
                return show_error('Input Error', 'Error in Skip Intervals. Value must be a non-negative integer.')

            return True

        def validate_module():
            """Validates the provided project path and entry module exist and contain executable code."""
            # Check if the project path exists
            project_path = Path(self.fields['project_path'])
            if not project_path.exists():
                return show_error('Project Does Not Exist', f'Project does not exist: {self.fields['project_path']}')

            # Check if the module path exists
            module_path = project_path / self.fields['entry_module']
            if not module_path.exists():
                return show_error('Module Not Found', f'Module not found: {module_path}')

            # Load module spec
            spec = importlib.util.spec_from_file_location(self.fields['entry_module'].rstrip('.py'), module_path)
            if spec is None or spec.loader is None:
                return show_error('Module Error', f'No valid module found at: {module_path}')

            return True

        validation_checks = [
            mandatory_fields,
            date_formats,
            time_format,
            set_next_run,  # Set next_run after validating date and time formats
            start_in_future,
            status_change_after_start,
            skips_is_int,
            validate_module
        ]

        for func in validation_checks:
            if not func():
                return False
        return True

    def submit(self):
        """Submits the task form to the task manager after converting DateTime objects to Unix Timestamps."""
        for field in ['next_run', 'status_change_date']:
            if self.fields[field]:
                self.fields[field] = self.fields[field].astimezone(ZoneInfo('UTC')).timestamp()

        # Add or edit task based on whether it's new
        if self.new_task:
            self.task_manager.add_task(new_task=self.fields)
        else:
            self.task_manager.edit_task(index=self.edit_index, updated_task=self.fields)
