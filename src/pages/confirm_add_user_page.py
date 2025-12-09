from nicegui import ui
from components import top_bar
from datetime import datetime, timedelta
import polars as pl
import random
import json
from src.methods.aws_functions import add_user_to_database

def confirm_add_user_page(participant_id, start_date, phone_number, lb_link, schedule):
    # Calculate end date as start date + 13 days
    end_date = datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=13)
    end_date = end_date.strftime('%Y-%m-%d')
    
    phone_number = f"+1{phone_number}" if not phone_number.startswith('+') else phone_number
    
    # Get Schedule Details from json
    path = 'src/methods/schedules.json'
    with open(path, 'r') as file:
        schedules = json.load(file)
        
        participant_schedule = schedules.get(schedule, {})
        schedule_df = pl.DataFrame(participant_schedule)
    
    def get_phase_breakdown():
        phase_1_end = datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=3)
        phase_2_end = phase_1_end + timedelta(days=8)
        phase_3_end = phase_2_end + timedelta(days=2)
        return phase_1_end, phase_2_end, phase_3_end
    
    def on_submit_handle():
        success, message = add_user_to_database(participant_id, start_date, end_date, phone_number, lb_link, schedule, send_randomizer)
        if success:
            ui.notify(f'{message}', type='positive', close_button=True, timeout=5000)
            ui.navigate.to('/')
        else:
            ui.notify(f'Failed to add user: {message}', type='negative', close_button=True, timeout=5000)
    
    top_bar('Confirm Add User Page')
    
    ui.label('Please confirm the following user details before adding:').classes('text-lg font-bold mb-5 w-full text-center pr-15')
    with ui.row().classes('w-full items-center gap-20 justify-center ml-20'):
        with ui.column().classes('pb-50'):
            ui.markdown(f'**Participant ID**: {participant_id}').classes('text-lg')
            ui.markdown(f'**Start Date**: {start_date}').classes('text-lg')
            ui.markdown(f'**End Date**: {end_date}').classes('text-lg')
            ui.markdown(f'**Phone Number**: {phone_number}').classes('text-lg')
            ui.markdown(f'**Leaderboard Link**: {lb_link}').classes('text-lg')
        with ui.column().classes(''):
            ui.markdown(f'**Schedule Type**: {schedule}').classes('text-lg')
            ui.table.from_polars(schedule_df).classes('w-auto items-center')
            ui.markdown('**Reminder Message Schedule (1s = send message, 0s = no message):**').classes('text-lg')
            send_randomizer, randomizer_df = message_shuffler()
            ui.table.from_polars(randomizer_df).classes('w-auto items-center')
            
            phase_1_end, phase_2_end, phase_3_end = get_phase_breakdown()
            ui.markdown(f'**Phase Breakdown:**').classes('text-lg')
            columns = [
                {'name': 'Phase1', 'label': 'Phase 1', 'field': 'Phase1', 'align': 'left'},
                {'name': 'Phase2', 'label': 'Phase 2', 'field': 'Phase2', 'align': 'left'},
                {'name': 'Phase3', 'label': 'Phase 3', 'field': 'Phase3', 'align': 'left'},
            ]
            rows = [
                {
                    'Phase1': f'{start_date} to {phase_1_end.strftime("%Y-%m-%d")}',
                    'Phase2': f'{(phase_1_end + timedelta(days=1)).strftime("%Y-%m-%d")} to {phase_2_end.strftime("%Y-%m-%d")}',
                    'Phase3': f'{(phase_2_end + timedelta(days=1)).strftime("%Y-%m-%d")} to {phase_3_end.strftime("%Y-%m-%d")}',
                }
            ]
            ui.table(columns=columns, rows=rows).classes('w-auto items-center align-center')
    with ui.row().classes('w-full justify-center mt-10 mb-20'):
                        ui.button('Go Back', on_click=lambda: ui.navigate.back()).props('color=red').classes('mr-10')
                        ui.button('Confirm and Add User', on_click=on_submit_handle).props('color=green').classes('mr-10')

def message_shuffler():
    send_randomizer = [1, 1, 1, 1, 0, 0, 0, 0] # 1s are send message, 0s are don't send message 
    random.shuffle(send_randomizer)
    
    randomizer_df = pl.DataFrame(data={'Day 4': send_randomizer[0],
                             'Day 5': send_randomizer[1],
                             'Day 6': send_randomizer[2],
                             'Day 7': send_randomizer[3],
                             'Day 8': send_randomizer[4],
                             'Day 9': send_randomizer[5],
                             'Day 10': send_randomizer[6],
                             'Day 11': send_randomizer[7]}
    )
    
    return send_randomizer, randomizer_df