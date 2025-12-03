from nicegui import ui

def main_page():
    dark = ui.dark_mode(True)
    
    with ui.row().classes('w-full justify-between items-center'):
        with ui.button(icon='menu'):
            with ui.menu():
                ui.menu_item('Homepage')
                ui.menu_item('Initialization')
                ui.menu_item('Add User')
                with ui.menu_item('View/Edit User', auto_close=False):
                    with ui.item_section().props('side'):
                        ui.icon('keyboard_arrow_right')
                    with ui.menu().props('anchor="top end" self="top start" auto-close'):
                        ui.menu_item("View User Details")
                        ui.menu_item("Edit User Information")
                        ui.menu_item("Delete User")
                with ui.menu_item('Participant Checks', auto_close=False):
                    with ui.item_section().props('side'):
                        ui.icon('keyboard_arrow_right')
                    with ui.menu().props('anchor="top end" self="top start" auto-close'):
                        ui.menu_item("Generate Daily Report")
                        ui.menu_item("Check Individual Compliance")
                ui.menu_item('Send Test SMS')
        
        ui.label('Project INSIGHT Part 3 Dashboard').classes('text-h6')
        
        ui.switch('Dark Mode').bind_value(dark)

main_page()
ui.run()
