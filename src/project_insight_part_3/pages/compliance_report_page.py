from nicegui import ui
import re
from .components import top_bar
from ..methods.compliance_methods import get_survey_send_times_all, get_participant_list, compliance_table_daily_report, merge_survey_data, contact_checks

def compliance_report_page():
    
    early_bird_df, standard_schedule_df, night_owl_df = None, None, None
    participant_df = None
    compliance_df = None
    did_not_do_lb = None
    two_NRs_in_a_row = None
    
    current_page = 1
    total_pages = 4
    
    top_bar('Compliance Report')

    with ui.row().classes('w-full justify-center gap-10'):
        with ui.column().classes('w-100 outline outline-cyan-500 outline-offset-10 rounded-lg items-center justify-left'):
            ui.label('Compliance Report').classes('text-lg font-bold mb-5')
            
            compliance_report_container = ui.column().classes('w-100 h-auto items-left justify-left')
            with compliance_report_container:
                with ui.input(label = 'Date (YYYY-MM-DD)', validation={'Must be a date in the format YYYY-MM-DD': lambda value: bool(re.match(r'^\d{4}-\d{2}-\d{2}$', value))}).classes('w-flex') as date_input:
                    with ui.menu().props('no-parent-event') as menu:
                        with ui.date().bind_value(date_input):
                            with ui.row().classes('justify-end'):
                                ui.button('Close', on_click=menu.close).props('flat')
                    with date_input.add_slot('append'):
                        ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
                ui.button('Generate Report', on_click=lambda: load_compliance_report()).classes('mb-3')
        
        compliance_summary_column = ui.column().classes('w-200 h-flex outline outline-cyan-500 outline-offset-10 rounded-lg items-center justify-left')
        compliance_summary_column.visible = False
        
        def update_content(page: int = 1):
            nonlocal current_page
            current_page = page
            compliance_summary_column.clear()
            with compliance_summary_column:
                if page == 2:
                    ui.label("Send Schedules").classes('text-lg font-bold mb-5')
                    content_container = ui.column().classes('w-full')
                    with content_container:
                        if early_bird_df is not None:
                            ui.markdown('#### Early Bird Schedule')
                            ui.table.from_polars(early_bird_df).classes('w-full')
                        if standard_schedule_df is not None:
                            ui.markdown('#### Standard Schedule')
                            ui.table.from_polars(standard_schedule_df).classes('w-full')
                        if night_owl_df is not None:
                            ui.markdown('#### Night Owl Schedule')
                            ui.table.from_polars(night_owl_df).classes('w-full')
                
                elif page == 1:
                    ui.label("Study Participants").classes('text-lg font-bold mb-5')
                    content_container = ui.column().classes('w-full')
                    with content_container:
                        if participant_df is not None:
                            ui.markdown(f"#### Not Started ({len(participant_df['not_started'])}):")
                            ui.table.from_polars(participant_df['not_started']).classes('w-full')
                            ui.markdown(f"#### Currently In Study ({len(participant_df['currently_in_study'])}):")
                            ui.table.from_polars(participant_df['currently_in_study']).classes('w-full')
                            ui.markdown(f"#### Completed ({len(participant_df['done_with_study'])}):")
                            ui.table.from_polars(participant_df['done_with_study']).classes('w-full')
                        else:
                            ui.label("No participant data available for the selected date.")
                
                elif page == 3:
                    ui.label("Compliance Summary").classes('text-lg font-bold mb-5')
                    content_container = ui.column().classes('w-full')
                    with content_container:
                        if compliance_df is not None:
                            ui.table.from_polars(compliance_df).classes('w-full')
                        else:
                            ui.label("No compliance data available for the selected date.")
                
                elif page == 4:
                    ui.label("Contact Checks").classes('text-lg font-bold mb-5')
                    ui.markdown("_Please double check the schedule that the participant is on and whether it's been an hour since the survey was sent to them. This log does not identify whether it's been an hour since the participant received the survey, just that they have not completed it and are either on their first or second NR._")

                    content_container = ui.column().classes('w-full')
                    with content_container:
                        # List
                        if did_not_do_lb is not None and len(did_not_do_lb) > 0:
                            ui.markdown(f"#### Participants who did not do LB ({len(did_not_do_lb)}):")
                            # list participants who did not do LB in markdown format
                            for participant in did_not_do_lb:
                                ui.markdown(f"- {participant}")
                        else:
                            pass
                        
                        if two_NRs_in_a_row is not None and len(two_NRs_in_a_row) > 0:
                            ui.markdown(f"#### Participants with 2 NRs in a row ({len(two_NRs_in_a_row)}):")
                            for participant in two_NRs_in_a_row:
                                ui.markdown(f"- {participant}")
                        else:
                            pass
                
                # Navigation buttons at bottom center
                with ui.row().classes('w-full justify-center mt-5 gap-2'):
                    for i in range(1, total_pages + 1):
                        if i == current_page:
                            ui.button(str(i), on_click=lambda p=i: update_content(p)).props('flat color=primary')
                        else:
                            ui.button(str(i), on_click=lambda p=i: update_content(p)).props('flat')
            
    def load_compliance_report():
        nonlocal early_bird_df, standard_schedule_df, night_owl_df
        nonlocal participant_df
        nonlocal compliance_df
        nonlocal did_not_do_lb, two_NRs_in_a_row
        
        date_value = date_input.value
        early_bird_df, standard_schedule_df, night_owl_df = get_survey_send_times_all(date_value)
        compliance_summary_column.visible = True
        
        participant_df = get_participant_list(date_value)
        merged_df = merge_survey_data()
        compliance_df = compliance_table_daily_report(date_value, participant_df, early_bird_df, standard_schedule_df, night_owl_df, merged_df)
        did_not_do_lb, two_NRs_in_a_row = contact_checks(compliance_df)
        
        update_content(1)  # Show the first page after loading data

        
        