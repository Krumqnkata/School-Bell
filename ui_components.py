"""
UI components for the School Bell application.
"""
import customtkinter
from tkinter import Canvas, Text, WORD
from config import GREEN, RED, BLUE, BG_WEEKDAYS
from datetime import datetime


def setup_left_panel(app):
    """Setup the left panel of the application."""
    app.left_panel = customtkinter.CTkFrame(app, fg_color="transparent")
    app.left_panel.grid(row=0, column=0, sticky="nswe", padx=20, pady=20)
    app.left_panel.grid_rowconfigure(14, weight=1) # Adjusted for new buttons

    customtkinter.CTkLabel(app.left_panel, text="СТАТУС:", font=customtkinter.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=(10, 5), sticky="w")
    app.status_label = customtkinter.CTkLabel(app.left_panel, text="СПРЯН", text_color=RED, font=customtkinter.CTkFont(size=18, weight="bold"))
    app.status_label.grid(row=1, column=0, padx=20, pady=5, sticky="w")

    customtkinter.CTkLabel(app.left_panel, text="Текущо време:", font=customtkinter.CTkFont(size=16)).grid(row=2, column=0, padx=20, pady=(20, 5), sticky="w")
    app.digital_clock_label = customtkinter.CTkLabel(app.left_panel, text="--:--:--", font=customtkinter.CTkFont(size=18, weight="bold"))
    app.digital_clock_label.grid(row=3, column=0, padx=20, pady=5, sticky="w")

    customtkinter.CTkLabel(app.left_panel, text="Следващ звънец:", font=customtkinter.CTkFont(size=16)).grid(row=4, column=0, padx=20, pady=(20, 5), sticky="w")
    app.next_bell_label = customtkinter.CTkLabel(app.left_panel, text="--:--:--", font=customtkinter.CTkFont(size=14, weight="bold"))
    app.next_bell_label.grid(row=5, column=0, padx=20, pady=5, sticky="w")

    customtkinter.CTkLabel(app.left_panel, text="Сила на звука:", font=customtkinter.CTkFont(size=16)).grid(row=6, column=0, padx=20, pady=(20, 5), sticky="w")
    
    volume_control_frame = customtkinter.CTkFrame(app.left_panel, fg_color="transparent")
    volume_control_frame.grid(row=7, column=0, padx=20, pady=5, sticky="ew")
    volume_control_frame.grid_columnconfigure(0, weight=1)
    
    app.volume_slider = customtkinter.CTkSlider(volume_control_frame, from_=0, to=1, command=app.set_volume)
    app.volume_slider.set(1.0)  # Set default volume to 100%
    app.volume_slider.grid(row=0, column=0, sticky="ew", padx=(0, 5))
    
    app.volume_percentage_label = customtkinter.CTkLabel(volume_control_frame, text="100%", width=40)
    app.volume_percentage_label.grid(row=0, column=1, sticky="w")

    app.quiet_mode_checkbox = customtkinter.CTkCheckBox(app.left_panel, text="Тих режим", variable=app.quiet_mode)
    app.quiet_mode_checkbox.grid(row=8, column=0, padx=20, pady=10, sticky="w")

    # New button to open schedule config editor
    app.open_schedule_config_button = customtkinter.CTkButton(app.left_panel, text="Настройки на графика", command=app.open_schedule_config_editor, width=180)
    app.open_schedule_config_button.grid(row=9, column=0, padx=20, pady=(20, 10))

    # Frame for manual ring controls
    manual_ring_frame = customtkinter.CTkFrame(app.left_panel, fg_color="transparent")
    manual_ring_frame.grid(row=10, column=0, padx=20, pady=10, sticky="ew")
    manual_ring_frame.grid_columnconfigure(0, weight=1)
    
    # Dropdown for selecting specific song
    app.manual_song_var = customtkinter.StringVar(value=app.song_list[0])
    app.manual_song_dropdown = customtkinter.CTkOptionMenu(manual_ring_frame, variable=app.manual_song_var, values=app.song_list, width=140)
    app.manual_song_dropdown.grid(row=0, column=0, sticky="ew", padx=(0, 10))

    app.manual_ring_button = customtkinter.CTkButton(manual_ring_frame, text="Пусни звънеца сега", command=app.manual_ring)
    app.manual_ring_button.grid(row=0, column=1, sticky="ew")

    # Buttons for editing specific schedules
    app.schedule_edit_buttons_frame = customtkinter.CTkFrame(app.left_panel, fg_color="transparent")
    app.schedule_edit_buttons_frame.grid(row=11, column=0, padx=20, pady=10, sticky="ew")
    app.schedule_edit_buttons_frame.grid_columnconfigure((0,1), weight=1)

    app.open_normal_schedule_editor_button = customtkinter.CTkButton(app.schedule_edit_buttons_frame, text="Редактирай Нормален График", command=app.open_normal_schedule_editor, width=180)
    app.open_normal_schedule_editor_button.grid(row=0, column=0, padx=(0,5))
    
    app.open_alternative_schedule_editor_button = customtkinter.CTkButton(app.schedule_edit_buttons_frame, text="Редактирай Алтернативен График", command=app.open_alternative_schedule_editor, width=180)
    app.open_alternative_schedule_editor_button.grid(row=0, column=1, padx=(5,0))

    app.start_stop_button = customtkinter.CTkButton(app.left_panel, text="СТАРТ", command=app.toggle_service, width=200)
    app.start_stop_button.grid(row=12, column=0, padx=20, pady=20, sticky="s")

    disclaimer_label = customtkinter.CTkLabel(app.left_panel, text="Важно: При промяна/добавяне на песни, рестартирайте програмата.", font=customtkinter.CTkFont(size=11, slant="italic"), text_color="yellow", wraplength=250)
    disclaimer_label.grid(row=13, column=0, padx=20, pady=(0, 10), sticky="s")

    app.about_button = customtkinter.CTkButton(app.left_panel, text="Относно", command=app.show_about, fg_color="transparent", hover_color="#555555", width=60)
    app.about_button.grid(row=14, column=0, padx=20, pady=(0, 20), sticky="s")


def setup_center_panel(app):
    """Setup the center panel of the application."""
    app.center_panel = customtkinter.CTkFrame(app, fg_color="transparent")
    app.center_panel.grid(row=0, column=1, sticky="nswe", padx=0, pady=20)
    app.center_panel.grid_rowconfigure(0, weight=1)
    app.log_box = Text(app.center_panel, wrap=WORD, state="disabled", bg="#2B2B2B", fg="white", bd=0, font=("Consolas", 11))
    app.log_box.grid(row=0, column=0, sticky="nswe")

    app.log_box.tag_config('timestamp', foreground='orange')
    app.log_box.tag_config('message', foreground='white')


def setup_right_panel(app):
    """Setup the right panel of the application."""
    app.right_panel = customtkinter.CTkFrame(app, fg_color="transparent")
    app.right_panel.grid(row=0, column=2, sticky="nswe", padx=20, pady=20)
    app.right_panel.grid_rowconfigure(1, weight=1)
    app.right_panel.grid_columnconfigure(0, weight=1)

    app.schedule_display_title = customtkinter.CTkLabel(app.right_panel, text="", font=customtkinter.CTkFont(size=16, weight="bold"))
    app.schedule_display_title.grid(row=0, column=0, padx=10, pady=(10, 10), sticky="w")
    app.schedule_display_frame = customtkinter.CTkScrollableFrame(app.right_panel, fg_color="transparent")
    app.schedule_display_frame.grid(row=1, column=0, sticky="nsew", padx=10)