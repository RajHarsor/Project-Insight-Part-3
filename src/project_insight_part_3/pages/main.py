# Use this to run from VSCode: python -m project_insight_part_3.pages.main

from nicegui import ui
import polars as pl

from ..methods.homepage_figures import pie_chart_progress, phase_breakdown_pie_chart, enrollment_progress_over_time
from ..methods.compliance_methods import get_participant_initials, merge_survey_data, match_initials_table
from ..methods.env_initialize import read_env_variables

from .components import top_bar
from .initialization_page import initialization_page
from .add_user_page import add_user_page
from .confirm_add_user_page import confirm_add_user_page
from .view_edit_user_page import view_edit_user_page
from .delete_user_page import delete_user_page
from .send_sms_page import send_sms_page
from .individual_compliance_check import individual_compliance_check_page


def register_pages() -> None:
    ui.page('/')(main_page)
    ui.page('/initialization')(initialization_page)
    ui.page('/add_user')(add_user_page)
    ui.page('/confirm_add_user')(confirm_add_user_page)
    ui.page('/view_edit_user')(view_edit_user_page)
    ui.page('/delete_user')(delete_user_page)
    ui.page('/send_sms')(send_sms_page)
    ui.page('/individual_compliance_check')(individual_compliance_check_page)


def main_page():
    top_bar('Project INSIGHT Part 3 Dashboard')

    with ui.row().classes('w-full justify-center gap-10'):
            
        with ui.column().classes('w-100 outline outline-cyan-500 outline-offset-10 rounded-lg items-center'):
            ui.label('Recent Activities').classes('text-lg font-bold mb-5')
            
            recent_activities_container = ui.column().classes('w-100 h-auto items-left justify-left')
            
            def load_recent_activities():
                recent_activities_container.clear()
                
                env_vars = read_env_variables()
                required_keys =  ['qualtrics_survey_p3_1a_path',
                    'qualtrics_survey_p3_1b_path',
                    'qualtrics_survey_p3_2a_path',
                    'qualtrics_survey_p3_2b_path',
                    'qualtrics_survey_p3_3_path',
                    'qualtrics_survey_p3_4_path',
                    'participant_db']
                
                if not all(key in env_vars and env_vars[key] for key in required_keys):
                    with recent_activities_container:
                        ui.label("Environment variables not properly set. Please initialize the environment.").classes('m-3').parent(recent_activities_container)
                        return
                
                participant_df_db = get_participant_initials()
                merged_df = merge_survey_data()
                matched_df = match_initials_table(merged_df, participant_df_db)
                
                if matched_df is None or matched_df.is_empty():
                    with recent_activities_container:
                        ui.label("No recent activities to display.").classes('m-3').parent(recent_activities_container)
                        return
                else:
                    try:
                        front_page_df = matched_df.select([
                            'Date/Time',
                            'Participant ID #',
                            'Initials',
                            'Survey Source'
                        ])
                        with recent_activities_container:
                            ui.table.from_polars(
                                front_page_df,
                                pagination=5
                            ).classes('w-100 h-auto')
                    except Exception as e:
                        print(f"Error displaying recent activities: {e}")
                        with recent_activities_container:
                            ui.label("Error displaying recent activities.").classes('m-3').parent(recent_activities_container)
            load_recent_activities()
                

        with ui.column().classes('w-100 outline outline-cyan-500 outline-offset-10 rounded-lg items-center'):
            ui.label('Participant Progress Overview').classes('text-lg font-bold justify-left')

            fig_container = ui.column().classes('w-100 h-auto items-center justify-center mr-7')
                
            def update_content():
                fig_container.clear()
                current = page_number.value if hasattr(page_number, 'value') else 1
                if current == 1:
                    with fig_container:
                        fig = pie_chart_progress()
                        ui.plotly(fig).classes('w-80 h-auto')
                elif current == 2:
                    with fig_container:
                        fig = phase_breakdown_pie_chart()
                        ui.plotly(fig).classes('w-80 h-auto')
                elif current == 3:
                    with fig_container:
                        fig = enrollment_progress_over_time()
                        fig.update_layout(margin=dict(l=20, r=20, t=0, b=0))
                        fig.update_layout(width=None, height=None, autosize=True)
                        fig = ui.plotly(fig).classes('w-80 h-auto')
                
            page_number = ui.pagination(1,3, direction_links=True, on_change=update_content).classes('justify-center items-center')
            update_content()

        with ui.column().classes('w-100 outline outline-cyan-500 outline-offset-10 rounded-lg items-center'):
            ui.label('Useful Links').classes('text-lg font-bold')
            ui.link('Project INSIGHT Website', 'https://projectinsighthealth.org/')
            ui.link('Project INSIGHT Google Drive','https://drive.google.com/drive/folders/1dHpQ_wOzshmQXk1aQO-cH4GCdB1QiGup?usp=drive_link')
            ui.link('Qualtrics', 'https://rowan.qualtrics.com/')
            ui.link('Project Repository', 'https://github.com/RajHarsor/Project-Insight-Part-3')
            ui.link('AWS Login', 'https://rowan.awsapps.com/start/')
            ui.link('NiceGUI Documentation', 'https://nicegui.io/documentation')
            ui.link('Tailwind CSS Documentation', 'https://tailwindcss.com/docs')


def main() -> None:
    register_pages()
    
    # Add reload = False before pushing new versions to production
    ui.run(port=8081, reload=True)

if __name__ in {"__main__", "__mp_main__"}:
    main()
