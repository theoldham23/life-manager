from typing import Literal, Union, Optional
import tkinter as tk
import pandas as pd
from app.user_interface.task_form.task_form import TaskUI
from app.task_manager.task_manager import TaskManager


class HomeUI:
    """A class to manage the Home user interface."""
    # Constants for the home window dimensions and fonts
    HOME_DIMS = {
        'width': 700,
        'height': 600
    }

    HOME_FONTS = {
        'title': ('Helvetica', int(HOME_DIMS['height'] / 22)),
        'header': ('Helvetica', int(HOME_DIMS['height'] / 43), 'bold'),
        'body': ('Helvetica', int(HOME_DIMS['height'] / 43))
    }

    def __init__(self, task_manager: TaskManager):
        """
        Initializes the user interface by unpacking the data from a TaskManager instance and loading the home page.
        :param task_manager: An instance of TaskManager to handle operations.
        """
        self.task_manager = task_manager

        self.root = tk.Tk()
        self.root.title('Life Manager')
        self.root.geometry(f'{self.HOME_DIMS['width']}x{self.HOME_DIMS['height']}')

        self.check_buttons = {}
        self.options_buttons = {}

        self.icons = {
            'add': tk.PhotoImage(file='user_interface/icons/add.png'),
            'play': tk.PhotoImage(file='user_interface/icons/play.png'),
            'pause': tk.PhotoImage(file='user_interface/icons/pause.png'),
            'view': tk.PhotoImage(file='user_interface/icons/view.png'),
            'edit': tk.PhotoImage(file='user_interface/icons/edit.png'),
            'delete': tk.PhotoImage(file='user_interface/icons/delete.png')
        }

        self.create_home()
        self.root.mainloop()

    def create_home(self):
        """Creates the home page for the UI. Calls create_frames to create the title_frame and outer_frame
        then passes them into the appropriate functions to be populated."""
        title_frame, outer_frame = self.create_frames(container=self.root, stack='v', proportions=[1, 9],
                                                      propagate=False)
        self.populate_title_frame(title_frame)

        column_frames = self.create_frames(container=outer_frame, stack='h', proportions=[1, 4, 3, 3, 3, 3, 3, 3],
                                           propagate=True)
        self.populate_column_frames(column_frames)

    def create_frames(self, container: Union[tk.Tk, tk.Widget], stack: Literal['v', 'h'], proportions: list[int],
                      propagate: Optional[bool] = True):
        """
        Creates a set of tkinter frames to fill the space of the parent container, either stacked vertically or
        horizontally.
        :param container: The parent container for the frames.
        :param stack: The orientation to stack the created frames, either 'v' for vertical or 'h' for horizontal.
        :param proportions: A tuple of integers representing the relative proportions of the created frames.
        :param propagate: Whether the parent container will propagate to fit the new frames. Default = True.
        :return: A list of tk.Frame instances created within the specified container.
        """
        frames = []
        for i, proportion in enumerate(proportions):
            frame = tk.Frame(container, width=self.HOME_DIMS['width'])
            frame.grid_propagate(propagate)

            if stack == 'v':
                frame.grid(row=i, column=0, sticky='nsew')
                container.grid_rowconfigure(i, weight=proportion)
                container.grid_columnconfigure(0, weight=1)
            elif stack == 'h':
                frame.grid(row=0, column=i, sticky='nsew')
                container.grid_rowconfigure(0, weight=1)
                container.grid_columnconfigure(i, weight=proportion)

            frames.append(frame)

        return frames

    def populate_title_frame(self, title_frame: tk.Frame):
        """Populates the title frame with a title and an add button."""
        # Configure grid layout
        title_frame.grid_rowconfigure(0, weight=1)
        title_frame.grid_columnconfigure(0, weight=1)  # Empty label column
        title_frame.grid_columnconfigure(1, weight=3)  # Title column
        title_frame.grid_columnconfigure(2, weight=1)  # Add button columns

        # Create title and add button
        tk.Label(title_frame, text='').grid(row=0, column=0, sticky='nsew')  # Empty label for alignment
        tk.Label(title_frame, text='Life Manager', font=self.HOME_FONTS['title']).grid(
            row=0, column=1, sticky='nsew')

        add_btn = tk.Button(title_frame, image=self.icons['add'], command=self.on_add_btn_press)
        add_btn.grid(row=0, column=2)

    def populate_column_frames(self, column_frames: list[tk.Frame]):
        """Populates each column frame with headers and body content based on the provided tasks DataFrame."""
        columns = [
            ('Notify', 'notify_on_run'),
            ('Project Name', 'project_name'),
            ('Status', 'status'),
            ('Change Date', 'status_change_date'),
            ('Intervals', 'schedule_interval'),
            ('Skips', 'skip_intervals'),
            ('Next Run', 'next_run'),
            ('Options', 'options')
        ]

        # Column Frames Content
        for i, (title, df_col) in enumerate(columns):
            column_frame = column_frames[i]

            # Create header
            tk.Label(column_frame, text=title, font=self.HOME_FONTS['header'], anchor='w', justify='left').grid(
                row=0, column=0, columnspan=4, sticky='w')

            # Populate body content
            tasks_df = self.task_manager.fetch_tasks()
            for index, row in tasks_df.iterrows():
                if title == 'Notify':
                    self.add_notify_check_buttons(column_frame, index, row[df_col])
                elif title == 'Options':
                    self.add_options_buttons(column_frame, index, row['status'])
                else:
                    self.populate_standard(column_frame, index, df_col)

    def add_notify_check_buttons(self, column_frame: tk.Frame, index: hash, pre_checked: int):
        """
        Adds a notify checkbox to the specified column frame.
        :param column_frame: The tk.Frame instance where the checkbox will be placed.
        :param index: The index of the task in the original tasks DataFrame.
        :param pre_checked: The value indicating whether the checkbox should be checked (1) or not (0).
        """
        check_var = tk.IntVar(value=int(pre_checked))
        check_button = tk.Checkbutton(column_frame, variable=check_var, onvalue=1, offvalue=0,
                                      command=lambda idx=index: self.on_notify_toggle(idx))
        check_button.grid(row=index + 1, column=0, padx=5, pady=(0, 4))
        self.check_buttons[index] = {'var': check_var, 'button': check_button}

    def add_options_buttons(self, column_frame: tk.Frame, index: hash, active_status: str):
        """
        Adds option buttons (icons) to the specified column frame.
        :param column_frame: The tk.Frame instance where the option buttons will be placed.
        :param index: The index of the task to associate with the buttons.
        :param active_status: A string containing the status for the task.
        """
        play_pause = 'pause' if active_status == 'Active' else 'play'
        icons = [play_pause, 'view', 'edit', 'delete']

        self.options_buttons[index] = {}
        for i, icon in enumerate(icons):
            icon_image = self.icons[icon]
            option_button = tk.Button(column_frame, image=icon_image, anchor='center',
                                      command=lambda idx=index, btn=icon: self.on_option_btn_press(idx, btn))
            option_button.grid(row=index + 1, column=i, pady=(0, 4), ipady=4, sticky='ew')
            self.options_buttons[index][icon] = {'button': option_button, 'icon': icon_image}

    def populate_standard(self, column_frame: tk.Frame, index: hash, df_col: str):
        """
        Adds a standard label to the specified column frame, displaying the task data.
        :param column_frame: The tk.Frame instance where the label will be placed.
        :param index: The row index for placing the label in the column frame.
        :param df_col: The column of the DataFrame.
        """
        tasks_df = self.task_manager.fetch_tasks()
        row_value = tasks_df.at[index, df_col]
        text_color = 'black'

        # Determine color of the text for status column
        if df_col == 'status':
            if row_value == 'Active':
                text_color = 'green'
            elif row_value == 'Paused':
                text_color = '#cdca09'

        # Format row_values in next_run and status_change_date columns as DateTime
        if df_col in ['next_run', 'status_change_date']:
            if pd.isna(row_value):
                row_value = ''
            else:
                row_value = row_value.to_pydatetime().strftime('%m/%d/%Y %I:%M %p')

        tk.Label(column_frame, text=row_value, font=self.HOME_FONTS['body'], anchor='w', justify='left',
                 fg=text_color,).grid(row=index + 1, column=0, pady=(0, 4), ipady=4, sticky='w')

    def on_add_btn_press(self):
        """Handles button press events for the add button"""
        TaskUI(self.task_manager, self.root)
        # Refresh home page
        self.create_home()

    def on_option_btn_press(self, index: int, btn: str):
        """
        Handles button press events for the options buttons (play, pause, view, edit, delete).
        :param index: The index of the task associated with the button.
        :param btn: The action associated with the pressed button.
        """
        match btn:
            case 'play' | 'pause':
                self.task_manager.toggle_status(index=index)
            case 'view':
                self.task_manager.view_task(index=index)
            case 'edit':
                TaskUI(task_manager=self.task_manager, root=self.root, edit_index=index)
            case 'delete':
                self.task_manager.delete_task(index=index)

        # Refresh home page
        self.create_home()

    def on_notify_toggle(self, index: int):
        """
        Handles check button interactions for the notify check button.
        :param index: The index of the task associated with the check button.
        """
        self.task_manager.toggle_notify(index=index)
