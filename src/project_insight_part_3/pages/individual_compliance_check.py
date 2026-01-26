from nicegui import ui
from .components import top_bar
import polars as pl
from datetime import datetime
from ..methods.compliance_methods import get_participant_initials, merge_survey_data, match_initials_table, get_participant_dynamo_db

def individual_compliance_check_page():
    top_bar('Individual Compliance Check')

    participant_id_input = ui.input(label='Enter Participant ID').props('clearable').classes('w-full mt-5')
    search_button = ui.button('Search', on_click=lambda: handle_search()).props('color=blue').classes('w-full mb-5')

    participant_info_container = ui.column().classes('w-full h-auto justify-center, items-center')
    participant_info_container.clear()

    with ui.row().classes('w-full justify-center gap-10'):
        
        # Compliance Data
        with ui.column().classes('w-100 outline outline-cyan-500 outline-offset-10 rounded-lg items-center'):
            #ui.label('Compliance Data').classes('text-lg font-bold mb-5')
            compliance_data_container = ui.column().classes('w-100 h-auto items-left justify-left')
            compliance_data_container.clear()
 
        # Timestamp Data
        with ui.column().classes('w-100 outline outline-cyan-500 outline-offset-10 rounded-lg items-center'):
            ui.label('Timestamp Data').classes('text-lg font-bold mb-5')
            timestamp_data_container = ui.column().classes('w-100 h-auto items-left justify-left')
            timestamp_data_container.clear()

    def handle_search():
        pid = participant_id_input.value.strip()
        pid = int(pid)
        if not pid:
            ui.notify('Please enter a valid Participant ID.', type='negative', close_button=True, timeout=5000)
            return
        
        # Clear previous data
        participant_info_container.clear()
        compliance_data_container.clear()
        timestamp_data_container.clear()
        
        with participant_info_container:
            participant_db = get_participant_initials()
            
            # Filter to get initials
            participant_row = participant_db.filter(pl.col('Participant ID #') == pid)
            #print(participant_row)
            if participant_row.is_empty():
                initials = 'N/A'
            else:
                initials = participant_row.select('Initials').to_series()[0]
            
            study_start_date, study_end_date, schedule_type = get_participant_dynamo_db(pid)
            
            # Calculate current day in study
            study_start_date = datetime.strptime(study_start_date, "%Y-%m-%d").strftime("%Y-%m-%d")           
            study_end_date = datetime.strptime(study_end_date, "%Y-%m-%d").strftime("%Y-%m-%d")
            current_day_in_study = (datetime.now() - datetime.strptime(study_start_date, "%Y-%m-%d")).days + 1
            
            ui.markdown(f'**Participant ID:** {pid}, **Initials:** {initials}, **Study Start Date:** {study_start_date}, **Study End Date:** {study_end_date}, **Current Day in Study:** {current_day_in_study}, **Current Compliance Rate:** [], **Total Compliance Rate:** []' ).classes('text-lg mb-5')
        # Fetch and display compliance data (placeholder logic)
        with compliance_data_container:
            ui.label(f"Compliance Data for {pid}").classes('m-3')
            # Here you would add the actual compliance data fetching and display logic
        
        # Fetch and display timestamp data (placeholder logic)
        with timestamp_data_container:
            ui.label(f"Timestamp Data for {pid}").classes('m-3')
            # Here you would add the actual timestamp data fetching and display logic