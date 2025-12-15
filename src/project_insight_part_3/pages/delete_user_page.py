from nicegui import ui
from src.project_insight_part_3.pages.components import top_bar
from src.project_insight_part_3.methods.aws_functions import get_user_info, delete_user_from_database

def delete_user_page():
    
    def handle_view_participant_information_button():
        participant_info_container.clear()
        user_info, message = get_user_info(participant_id_input.value)
        if user_info:
            with participant_info_container:
                ui.markdown('#### Participant Information:')
                ui.markdown(f'- **Participant ID**: {user_info.get("participant_id", "N/A")}')
                ui.markdown(f'- **Start Date**: {user_info.get("start_date", "N/A")}')
                ui.markdown(f'- **End Date**: {user_info.get("end_date", "N/A")}')
                ui.markdown(f'- **Phone Number**: {user_info.get("phone_number", "N/A")}')
                ui.markdown(f'- **Leaderboard Link**: {user_info.get("leaderboard_link", "N/A")}')
                ui.markdown(f'- **Schedule Type**: {user_info.get("schedule_type", "N/A")}')
                # Convert message_randomizer list to string for better display
                if isinstance(user_info.get("message_randomizer"), list):
                    user_info["message_randomizer"] = ', '.join(map(str, user_info["message_randomizer"]))
                ui.markdown(f'- **Message Randomizer** (1 is send message, 0 is do not send message): {user_info.get("message_randomizer", "N/A")}')
                ui.button('Delete Participant', on_click=lambda: handle_delete_participant_button(participant_id_input.value)).props('color=red').classes('w-100')
        else:
            ui.notify(message, type='negative', close_button=True, timeout=5000)
                
        def handle_delete_participant_button(participant_id):
            
            def confirm_delete_participant(participant_id, dialog):
                success, message = delete_user_from_database(participant_id)
                if success:
                    ui.notify(f'Participant {participant_id} deleted successfully!', type='positive', close_button=True, timeout=5000)
                    participant_info_container.clear()
                    ui.navigate.to('/')
                else:
                    ui.notify(f'Failed to delete participant {participant_id}: {message}', type='negative', close_button=True, timeout=5000)
                dialog.close()
                
            with ui.dialog() as dialog, ui.card():
                ui.label(f'Are you sure you want to delete participant {participant_id}? This action cannot be undone.')
                with ui.row().classes('justify-center gap-4 w-full'):
                    ui.button('Cancel', on_click=dialog.close).props('flat')
                    ui.button('Delete', on_click=lambda: confirm_delete_participant(participant_id, dialog)).props('color=red')
            
            dialog.open()
            

    
    top_bar('Delete Participant')
    
    with ui.row().classes('w-full justify-center gap-20'):
        with ui.column().classes():
            ui.markdown('#### View Participant Information').classes('text-lg font-bold w-100')
            participant_id_input = ui.input(label='Participant ID', validation= {'Must be a number': lambda value: value.isdigit()}).classes('w-100')
            ui.button('Search For Participant', on_click=handle_view_participant_information_button).props('color=blue').classes('w-100')
        with ui.column().classes():
            participant_info_container = ui.column().classes('w-100')
            