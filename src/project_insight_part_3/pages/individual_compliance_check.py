from nicegui import ui
from .components import top_bar
import polars as pl
from datetime import datetime
import plotly.graph_objects as go
import json
from importlib.resources import files
from ..methods.compliance_methods import get_participant_initials, get_participant_dynamo_db, get_survey_send_times, generate_compliance_table_individual, calculate_compliance_percentage, compliance_over_time_plot

def individual_compliance_check_page():
    top_bar('Individual Compliance Check')

    participant_id_input = ui.input(label='Enter Participant ID').props('clearable').classes('w-full mt-5')
    ui.button('Search', on_click=lambda: handle_search()).props('color=blue').classes('w-full mb-5')

    participant_info_container = ui.column().classes('w-full h-auto justify-center items-center')
    participant_info_container.visible = False
    
    compliance_df = None
    survey_send_df = None
    schedule_type = None

    with ui.row().classes('w-full justify-center gap-10'):

        with ui.column().classes('w-2/3 outline outline-cyan-500 outline-offset-10 rounded-lg items-center') as compliance_section:
            compliance_section.visible = False
            compliance_data_container = ui.column().classes('w-full h-auto items-center justify-center')
            

            def update_content(page: int = 1):
                nonlocal compliance_df
                nonlocal survey_send_df
                nonlocal schedule_type
                
                compliance_data_container.clear()
                with compliance_data_container:
                    if page == 1:
                        ui.label("Compliance Data Individual").classes('text-lg font-bold mb-5')
                        if compliance_df is not None and not compliance_df.is_empty():
                                #compliance_df = generate_compliance_table_individual(int(participant_id_input.value))
                                ui.table.from_polars(compliance_df).classes('w-full')
                                
                                info_container.clear()
                                with info_container:
                                    ui.markdown('**Legend:**')
                                    ui.markdown('**✓** = Completed on time')
                                    ui.markdown('**✗** = Not completed or completed late')
                                    ui.markdown('**NR** = No Response')
                                    ui.markdown('**SR** = Single Response')
                                    ui.markdown('**MR** = Multiple Responses')
                        else:
                            ui.label("No participant selected.").classes('m-3')
                            return

                    elif page == 2:
                        ui.label("Survey Send Times").classes('text-lg font-bold mb-5')
                        if survey_send_df is None or survey_send_df.is_empty():
                            survey_send_df = get_survey_send_times(int(participant_id_input.value))
                        #survey_send_df = get_survey_send_times(int(participant_id_input.value))
                        ui.table.from_polars(survey_send_df).classes('w-full')
                        
                        info_container.clear()
                        with info_container:
                            schedule = schedule_type
                            ui.markdown('**Send Schedule**').classes('text-lg font-bold mb-2')
                            
                            schedules_path = files("project_insight_part_3.methods").joinpath("schedules.json")
                            with schedules_path.open("r", encoding="utf-8") as file:
                                schedules = json.load(file)
            
                            participant_schedule = schedules.get(schedule, {})
                            schedule_df = pl.DataFrame(participant_schedule)
                            ui.table.from_polars(schedule_df).classes('w-full')
                            ui.markdown('All times are EST')
                    elif page == 3:
                        ui.label("Compliance Data Plot").classes('text-lg font-bold mb-5')
                        try:
                            compliance_df = calculate_compliance_percentage(compliance_df)
                            fig = compliance_over_time_plot(compliance_df)
                            ui.plotly(fig)
                            
                            info_container.clear()
                            with info_container:
                                ui.markdown('**Compliance Percentage**: Daily Compliance Percentage').classes('justify-left items-left')
                                ui.markdown('**Rolling Average**: Rolling Average based on the number of days completed in the study (e.g. if participant is on day 10, it will be a rolling average of the past 10 days)').classes('justify-left items-left')
                                
                                
                        except Exception as e:
                            ui.notify(f"Error calculating compliance percentage: {e}", type='negative', close_button=True, timeout=5000)
                            return
                        

            # place pagination below the content
            pagination = ui.pagination(1, 3, direction_links=True,
                                       on_change=lambda e: update_content(e.value)).classes('justify-center items-center mt-4')
            update_content(1)

        with ui.column().classes('w-100 outline outline-cyan-500 outline-offset-10 rounded-lg items-center') as info_section:
            info_section.visible = False
            ui.label('Info Container').classes('text-lg font-bold mb-5')
            info_container = ui.column().classes('w-100 h-auto items-center justify-center')
            
                

    def handle_search():
        nonlocal compliance_df
        nonlocal survey_send_df
        nonlocal schedule_type
        raw = participant_id_input.value or ''
        if not raw.strip():
            ui.notify('Please enter a valid Participant ID.', type='negative', close_button=True, timeout=5000)
            return
        try:
            pid = int(raw.strip())
        except ValueError:
            ui.notify('Please enter a valid Participant ID.', type='negative', close_button=True, timeout=5000)
            return
    
        try:
            participant_db = get_participant_initials()
            participant_row = participant_db.filter(pl.col('Participant ID #') == pid)
            
            if participant_row.is_empty():
                ui.notify(f'Participant ID {pid} not found in database.', type='negative', close_button=True, timeout=5000)
                return
                
            initials = participant_row.select('Initials').to_series()[0]
            
            study_start_date, study_end_date, schedule_type = get_participant_dynamo_db(pid)
            
            if participant_id_input.value:
                compliance_df = generate_compliance_table_individual(int(participant_id_input.value))
                survey_send_df = get_survey_send_times(int(participant_id_input.value))
                
                # Make sure the compliance_df has the same empty for corresponding cells (shouldn't show NR for surveys not sent yet)
                if compliance_df is not None and survey_send_df is not None:
                    
                    survey_send_df = survey_send_df.with_columns(
                        pl.col("Date").str.to_date()
                        
                        )
                    
                    send_cols = [c for c in survey_send_df.columns if c != "Date"]
                    join_df = compliance_df.join(
                        survey_send_df,
                        on="Date",
                        how="left",
                        suffix="_send"
                    )
                    exprs = [pl.col("Date")]
                    for col in send_cols:
                        if col in compliance_df.columns:
                            exprs.append(
                                pl.when(pl.col(f"{col}_send").is_null())
                                .then(None)
                                .otherwise(pl.col(col))
                                .alias(col)
                            )
                    compliance_df = join_df.select(exprs)
                    
                    # Calculate current compliance rate (only for dates <= today)
                    today = datetime.now().date()
                    past_df = compliance_df.filter(pl.col("Date") <= today)
                    
                    total_cells = 0
                    completed_cells = 0
                    for col in past_df.columns:
                        if col != "Date":
                            col_series = past_df[col]
                            non_null = col_series.is_not_null().sum()
                            total_cells += non_null
                            completed_cells += col_series.str.starts_with("✓").sum()
                    
                    current_compliance_rate = (completed_cells / total_cells * 100) if total_cells > 0 else 0
                    total_compliance = (completed_cells / 56 * 100) if total_cells > 0 else 0
                
            compliance_section.visible = True
            info_section.visible = True
            participant_info_container.visible = True

        except KeyError as e:
            ui.notify(f"Participant {pid} not found in DynamoDB: {e}", type='negative', close_button=True, timeout=5000)
            return
        except Exception as e:
            ui.notify(f"Error loading participant data: {e}", type='negative', close_button=True, timeout=5000)
            return

        participant_info_container.clear()
        compliance_data_container.clear()
        info_container.clear()

        pagination.value = 1
        update_content(1)

        with participant_info_container:
            study_start_date = datetime.strptime(study_start_date, "%Y-%m-%d")
            study_end_date = datetime.strptime(study_end_date, "%Y-%m-%d")
            current_day_in_study = (datetime.now() - study_start_date).days + 1

            ui.markdown(
                f'**Participant ID:** {pid}, **Initials:** {initials}, '
                f'**Study Start Date:** {study_start_date:%Y-%m-%d}, '
                f'**Study End Date:** {study_end_date:%Y-%m-%d}, '
                f'**Schedule Type:** {schedule_type}, '
                f'**Current Day in Study:** {current_day_in_study}, '
                f'**Current Compliance Rate:** {current_compliance_rate:.2f}%, **Total Compliance Rate:** {total_compliance:.2f}%'
            ).classes('text-lg mb-5')

