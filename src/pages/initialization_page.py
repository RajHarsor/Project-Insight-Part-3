from nicegui import ui
from components import top_bar
from src.methods.env_initialize import check_env_file_exists, check_env_variables

def initialization_page():
    top_bar('Initialization Page')
    
    with ui.row().classes('w-full justify-between items-center mt-8'):
        update_credential_button = ui.button('Update Credentials', on_click=lambda: ui.navigate.to('/initialization/update_credentials')).props('color=orange')
        setup_credential_button = ui.button('Setup Credentials', on_click=lambda: ui.navigate.to('/initialization/setup_credentials')).props('color=orange')
    
    update_credential_button.disable()
    setup_credential_button.disable()
    
    async def validate_env_variables():
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
            ui.notify('Environment file does not exist.', type='negative', close_button=True, timeout=5000)
    
    ui.timer(0.5, validate_env_variables, once=True)