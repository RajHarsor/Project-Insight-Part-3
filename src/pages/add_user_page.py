from nicegui import ui
from components import top_bar
from datetime import datetime
import re

def add_user_page():
    top_bar('Add User Page')
    
    with ui.column().classes('items-center w-full'):
        participant_id = ui.input(label='Participant ID', validation={'Must be an integer': lambda value: value.isdigit()}).classes('w-300')
        with ui.input('Start Date', validation={'Must be a date in the format YYYY-MM-DD': lambda value: bool(re.match(r'^\d{4}-\d{2}-\d{2}$', value))}).classes('w-300') as date_input:
            with ui.menu().props('no-parent-event') as menu:
                with ui.date().bind_value(date_input):
                    with ui.row().classes('justify-end'):
                        ui.button('Close', on_click=menu.close).props('flat')
            with date_input.add_slot('append'):
                ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
        phone_number = ui.input(label='Phone Number', placeholder='e.g., +1234567890', validation={'Must be in international format starting with +': lambda value: re.match(r'^\+\d{10,15}$', value) is not None}).classes('w-300')
        lb_link = ui.input(label='Leaderboard Link').classes('w-300')
        schedule_select = ui.select(label='Schedule', options=['Early Bird Schedule', 'Standard Schedule', 'Night Owl Schedule']).classes('w-300')
        submit_button = ui.button('Add User', on_click=lambda: go_to_confirm_add_user_page(participant_id.value, date_input.value, phone_number.value, lb_link.value, schedule_select.value)).props('color=green').classes('mt-5 w-300')
        
def go_to_confirm_add_user_page(participant_id, start_date, phone_number, lb_link, schedule):
    ui.navigate.to(f'/confirm_add_user?participant_id={participant_id}&start_date={start_date}&phone_number={phone_number}&lb_link={lb_link}&schedule={schedule}')