from pathlib import Path
from typing import List
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from app.task_manager.task_manager import TaskManager
from app.user_interface.task_form.task_form_manager import TaskFormManager


class TaskUI:
    """A class to manage the Task user interface. Used to add a new task or to edit an existing task."""
    def __init__(self, task_manager: TaskManager, root: tk.Tk, edit_index: int = None):
        """
        Initializes the user interface by unpacking the data from a TaskManager instance and loading the Tasks page.
        :param task_manager: An instance of TaskManager to handle operations.
        :param root: The tk.Tk root of the Home page.
        :param edit_index: Optionally, pass an index for existing task dictionary to automatically populate fields. This
        will also call task_manager.edit() to save over the existing task instead of creating a new task.
        """
        self.task_manager = task_manager
        self.edit_index = edit_index
        self.form_manager = TaskFormManager(self.task_manager, self.edit_index)

        self.row = 0

        self.browse_btn = None
        self.entry_module_combo = None
        self.clear_project_path_btn = None

        self.form_inputs = {}

        self.popup_form = tk.Toplevel(root)
        self.popup_form.title('Task Form')

        self.new_task_form()

    def new_task_form(self):
        """Opens the task form window."""
        # Project Name
        project_name_entry = self.create_labeled_entry(
            label_text='Project Name:',
            default_value=self.form_manager.fields['project_name']
        )
        self.form_inputs['project_name'] = project_name_entry
        self.row += 1

        # Project Path
        self.create_project_path_widgets()
        self.row += 1

        # Entry Module
        self.entry_module_combo = self.create_labeled_combobox(
            label_text='Entry Module:',
            values=[],
            default_value=self.form_manager.fields['entry_module']
        )

        if self.form_manager.fields['project_path']:
            self.entry_module_combo.state(['!disabled'])
        else:
            self.entry_module_combo.state(['disabled'])

        self.form_inputs['entry_module'] = self.entry_module_combo
        self.row += 1

        # Start Date
        start_date_entry = self.create_labeled_entry(
            label_text='Start Date:',
            default_value=self.form_manager.fields['start_date']
        )
        self.form_inputs['start_date'] = start_date_entry
        self.row += 1

        # Start Time
        start_time_entry = self.create_labeled_entry(
            label_text='Start Time:',
            default_value=self.form_manager.fields['start_time'],
            entry_width=15,
            entry_span=1
        )
        self.form_inputs['start_time'] = start_time_entry

        # AM/PM
        am_pm_combo = ttk.Combobox(
            self.popup_form,
            values=['AM', 'PM'],
            width=4,
            state='readonly'
        )
        am_pm_combo.grid(row=self.row, column=2)
        am_pm_combo.set(self.form_manager.fields['am_pm'])
        self.form_inputs['am_pm'] = am_pm_combo
        self.row += 1

        # Schedule Interval
        schedule_values = ['Minutes', 'Hours', 'Days', 'Weeks', 'Months', 'Years']
        schedule_interval_combo = self.create_labeled_combobox(
            label_text='Schedule Interval:',
            values=schedule_values,
            default_value=self.form_manager.fields['schedule_interval']
        )
        self.form_inputs['schedule_interval'] = schedule_interval_combo
        self.row += 1

        # Skip Intervals
        skip_intervals_entry = self.create_labeled_entry(
            label_text='Skip Intervals:',
            default_value=self.form_manager.fields['skip_intervals']
        )
        self.form_inputs['skip_intervals'] = skip_intervals_entry
        self.row += 1

        # Status Change Date
        status_change_date_entry = self.create_labeled_entry(
            label_text='Status Change Date:',
            default_value=self.form_manager.fields['status_change_date']
        )
        self.form_inputs['status_change_date'] = status_change_date_entry
        self.row += 1

        # Notify On Run
        notify_on_run_label = tk.Label(self.popup_form, text='Notify on Run')
        notify_on_run_var = tk.IntVar(value=self.form_manager.fields['notify_on_run'])
        notify_on_run_check_btn = tk.Checkbutton(self.popup_form, variable=notify_on_run_var, onvalue=1, offvalue=0)
        notify_on_run_label.grid(row=self.row, column=0, sticky='e')
        notify_on_run_check_btn.grid(row=self.row, column=1, sticky='w')
        self.form_inputs['notify_on_run'] = notify_on_run_var
        self.row += 1

        # Submit
        submit_btn = tk.Button(self.popup_form, text="Submit", command=self.on_submit)
        submit_btn.grid(row=self.row, column=0, columnspan=3, pady=10)

        self.popup_form.wait_window()

    def create_labeled_entry(self, label_text: str, default_value: str, entry_width: int = 20,
                             entry_span: int = 2) -> tk.Entry:
        """
        Creates a tkinter Label and a ttk Entry in the specified parent container.
        :param label_text: The text to display on the label.
        :param default_value: The value to be set as the default selected option in the Entry. Default is None.
        :param entry_width: The width of the Entry.
        :param entry_span: The number of columns the Entry will span. Default is 2.
        :return: The created Entry widget instance.
        """
        label = tk.Label(self.popup_form, text=label_text)
        entry = ttk.Entry(self.popup_form, width=entry_width)
        label.grid(row=self.row, column=0, sticky='e')
        entry.grid(row=self.row, column=1, columnspan=entry_span, sticky='ew')
        entry.insert(0, default_value)

        return entry

    def create_labeled_combobox(self, label_text: str, values: List[str], default_value: str = None,
                                combo_span: int = 2) -> ttk.Combobox:
        """
        Creates a tkinter Label and a read-only ttk Combobox in the specified parent container,
        places them in the given row, and optionally sets a default value for the Combobox.
        :param label_text: The text to display on the label.
        :param values: A list of options to populate the Combobox.
        :param default_value: The value to be set as the default selected option in the Combobox. Default is None.
        :param combo_span: The number of columns the Combobox will span. Default is 2.
        :return: The created Combobox widget instance.
        """
        label = tk.Label(self.popup_form, text=label_text)
        combo = ttk.Combobox(self.popup_form, values=values, state='readonly')
        label.grid(row=self.row, column=0, sticky='e')
        combo.grid(row=self.row, column=1, columnspan=combo_span, sticky='ew')
        combo.set(default_value)

        return combo

    def create_project_path_widgets(self):
        """Creates widgets for project_path"""
        project_path_label = tk.Label(self.popup_form, text='File Path:')
        self.browse_btn = ttk.Button(self.popup_form, text='Browse', command=self.on_browse_btn_press)
        self.clear_project_path_btn = ttk.Button(self.popup_form, text='Clear', command=self.on_clear_btn_press)

        project_path_label.grid(row=self.row, column=0, sticky='e')
        self.browse_btn.grid(row=self.row, column=1, sticky='w')
        self.clear_project_path_btn.grid(row=self.row, column=2, sticky='w')

        if self.form_manager.fields['project_path']:
            self.browse_btn.state(['disabled'])
        else:
            self.browse_btn.state(['!disabled'])

    def on_browse_btn_press(self):
        """Opens a file dialog for the user to select a directory. Sets project_path to the result and
        enables self.entry_module_combo."""
        project_path = filedialog.askdirectory()
        if project_path:
            self.form_manager.fields['project_path'] = project_path
            modules = self.list_modules()

            if modules:
                self.entry_module_combo['values'] = modules
                self.entry_module_combo.state(['!disabled'])
                # Default to main.py if it exists, otherwise first module in project
                self.entry_module_combo.set('main.py' if 'main.py' in modules else modules[0])

                self.browse_btn.state(['disabled'])
                self.clear_project_path_btn.state(['!disabled'])
            else:
                self.form_manager.project_path = None
                messagebox.showerror('Input Error', 'Selected project has no modules.')

    def list_modules(self) -> List[str]:
        """
        Finds the modules within the project path.
        :return: A list of modules.
        """
        project_path = Path(self.form_manager.fields['project_path'])  # Convert to a Path object
        return [
            str(file.relative_to(project_path)).replace('/', '.').replace('\\', '.')
            for file in project_path.glob('*.py')
        ]

    def on_clear_btn_press(self):
        """Resets the project path and entry module fields."""
        self.form_manager.fields['project_path'] = ''
        self.entry_module_combo['values'] = []
        self.entry_module_combo.state(['disabled'])
        self.entry_module_combo.set('')
        self.browse_btn.state(['!disabled'])
        self.clear_project_path_btn.state(['!disabled'])

    def on_submit(self):
        """
        Gathers user input from form widgets, validates the data, processes it,
        and adds a new task if validation is successful. Then closes the form.
        """
        for key in self.form_inputs:
            self.form_manager.fields[key] = self.form_inputs[key].get()

        if self.form_manager.validate():
            self.form_manager.submit()
            self.popup_form.destroy()
