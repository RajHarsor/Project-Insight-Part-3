from nicegui import ui
from .components import top_bar
from ..methods.env_initialize import check_env_file_exists, check_env_variables, create_env_file, update_env_variable, read_env_variables

def initialization_page():
    
    setup_container = None

    def refresh_env_display():
        """Refresh the environment variable display"""
        env_vars = read_env_variables()
        env_var_display_container.clear()
        with env_var_display_container:
            with ui.column().classes('mt-0'):
                ui.label('Current Part 3 Environment Variables:').classes('text-lg font-bold mb-2 w-100')
                for key, value in env_vars.items():
                    if key in ['aws_access_key_id', 'aws_secret_access_key', 'insight_p3_table_name',
                               'qualtrics_survey_p3_1a_path', 'qualtrics_survey_p3_1b_path',
                               'qualtrics_survey_p3_2a_path', 'qualtrics_survey_p3_2b_path',
                               'qualtrics_survey_p3_3_path', 'qualtrics_survey_p3_4_path',
                               'participant_db']:
                        ui.label(f'- {key}: {value}')

    def update_page():
        nonlocal setup_container
        update_credential_button.disable()
        setup_credential_button.disable()
        
        if setup_container:
            setup_container.clear()
            env_var_display_container.clear()
        
        with setup_container:
            with ui.row().classes('justify-center mt-5 gap-10 justify-start'):
                with ui.column().classes('items-right mt-5 gap-1'):
                    ui.label('Choose Variable to Update').classes('text-lg font-bold mb-2 w-100')
                    variable_select = ui.select(['AWS Access Key ID (aws_access_key_id)', 'AWS Secret Access Key (aws_secret_access_key)', 'DynamoDB Table Name (insight_p3_table_name)',
                                                    'Qualtrics Survey 1A Path (qualtrics_survey_p3_1a_path)', 'Qualtrics Survey 1B Path (qualtrics_survey_p3_1b_path)',
                                                    'Qualtrics Survey 2A Path (qualtrics_survey_p3_2a_path)', 'Qualtrics Survey 2B Path (qualtrics_survey_p3_2b_path)',
                                                    'Qualtrics Survey 3 Path (qualtrics_survey_p3_3_path)',
                                                    'Qualtrics Survey 4 Path (qualtrics_survey_p3_4_path)',
                                                    'Participant Database Path (participant_db)']).classes('w-100')
                new_value_input = ui.input(label='New Value').classes('w-100 mt-15')

                def on_submit():
                    update_env_variable(variable_name(), new_value_input.value)
                    ui.notify(f'Updated {variable_name()} successfully!', type='positive', close_button=True, timeout=5000)
                    env_vars = read_env_variables()
                    env_display_container.clear()
                    with env_display_container:
                        with ui.column().classes('mt-5'):
                            ui.label('New Environment Variables:').classes('text-lg font-bold mb-2 w-100 outline outline-cyan-500 outline-offset-10 rounded-lg')
                            for key, value in env_vars.items():
                                ui.label(f'- {key}: {value}')

                # get the variable name from the select value by extracting the text inside the parentheses
                variable_name = lambda: variable_select.value.split('(')[1].strip(')')
                submit_button = ui.button('Submit', on_click=on_submit).props('color=green').classes('mt-10 w-full')
                submit_button.disable()
                
                def validate_new_input():
                    if new_value_input.value and len(new_value_input.value) > 2:
                        submit_button.enable()
                    else:
                        submit_button.disable()
                
                new_value_input.on_value_change(validate_new_input)
                
            env_display_container = ui.column().classes('mt-5')


                    
    def setup_page():
        nonlocal setup_container
        update_credential_button.disable()
        setup_credential_button.disable()
        
        if setup_container:
            setup_container.clear()
            # Removed env_var_display_container.clear() to keep existing vars visible during setup
        
        with setup_container:
            with ui.row().classes('justify-center mt-5 gap-30'):
                with ui.column().classes('items-right mt-5 gap-1'):
                    ui.label('Credential Setup').classes('text-lg font-bold mb-2')
                    aws_access_key = ui.input(label='AWS Access Key ID').classes('w-100')
                    aws_secret_key = ui.input(label='AWS Secret Access Key').classes('w-100')
                    dynamodb_table_name = ui.input(label='DynamoDB Table Name').classes('w-100')
                with ui.column().classes('items-right mt-2 gap-1'):
                    ui.label('Optional Settings - Needed for Reports').classes('text-lg font-bold mb-2')
                    survey_1a_path = ui.input(label='Survey 1A Path').classes('w-100')
                    survey_1b_path = ui.input(label='Survey 1B Path').classes('w-100')
                    survey_2a_path = ui.input(label='Survey 2a Path').classes('w-100')
                    survey_2b_path = ui.input(label='Survey 2b Path').classes('w-100')
                    survey_3_path = ui.input(label='Survey 3 Path').classes('w-100')
                    survey_4_path = ui.input(label='Survey 4 Path').classes('w-100')
                    participant_db_path = ui.input(label='Participant Database Path').classes('w-100')
            
            def validate_mandatory_fields():
                if aws_access_key.value and aws_secret_key.value and dynamodb_table_name.value:
                    submit_button.enable()
                else:
                    submit_button.disable()
            
            def handle_submit():
                submit_button.disable()
                create_env_file(
                    aws_access_key.value,
                    aws_secret_key.value,
                    dynamodb_table_name.value,
                    survey_1a_path.value,
                    survey_1b_path.value,
                    survey_2a_path.value,
                    survey_2b_path.value,
                    survey_3_path.value,
                    survey_4_path.value,
                    participant_db_path.value
                )
                ui.notify('Environment file created successfully!', type='positive', close_button=True, timeout=5000)
            
            submit_button = ui.button('Submit', on_click=handle_submit).props('color=green').classes('mt-15 w-full')
            submit_button.disable()  # Start disabled

            # Add validation on input change using on_value_change which is safer for inputs
            aws_access_key.on_value_change(lambda e: validate_mandatory_fields())
            aws_secret_key.on_value_change(lambda e: validate_mandatory_fields())
            dynamodb_table_name.on_value_change(lambda e: validate_mandatory_fields())

    top_bar('Initialization Page')
    
    with ui.row().classes('justify-center mt-5 gap-15'):
        with ui.column().classes('items-right mt-0 gap-4'):
            update_credential_button = ui.button('Update Credentials', on_click=lambda: update_page()).props('color=blue')
            setup_credential_button = ui.button('Setup Credentials', on_click=lambda: setup_page()).props('color=blue')
        setup_container = ui.column()
        env_var_display_container = ui.column().classes('text-left outline outline-cyan-500 outline-offset-10 rounded-lg')
        # Get current env variables and display
        env_vars = read_env_variables()
        #FIXME: This should only display the env variables of interest and not all of them in the .env file
        with env_var_display_container:
            with ui.column().classes('mt-0'):
                ui.label('Current Part 3 Environment Variables:').classes('text-lg font-bold mb-2 w-100')
                for key, value in env_vars.items():
                    if key in ['aws_access_key_id', 'aws_secret_access_key', 'insight_p3_table_name',
                               'qualtrics_survey_p3_1a_path', 'qualtrics_survey_p3_1b_path',
                               'qualtrics_survey_p3_2a_path', 'qualtrics_survey_p3_2b_path',
                               'qualtrics_survey_p3_3_path', 'qualtrics_survey_p3_4_path',
                               'participant_db']:
                        ui.label(f'- {key}: {value}')
        
    update_credential_button.disable()
    setup_credential_button.disable()
    
    def validate_env_variables():
        exists = check_env_file_exists()
        var_exists, var_message = check_env_variables()
        
        if exists and var_exists:
            update_credential_button.enable()
            setup_credential_button.disable()
            ui.notify('All mandatory environment variables are set correctly.', type='positive', close_button=True, timeout=5000)
        elif exists and not var_exists:
            update_credential_button.enable()
            setup_credential_button.disable()
            ui.notify(var_message, type='warning', close_button=True, timeout=5000)
        else:
            update_credential_button.disable()
            setup_credential_button.enable()
            ui.notify('Environment file does not exist. Please set up your credentials.', type='negative', close_button=True, timeout=5000)
    
        
    ui.timer(0.5, validate_env_variables, once=True)