from nicegui import ui

def menu():
    with ui.button(icon='menu'):
        with ui.menu():
            ui.menu_item('Homepage', on_click=lambda: ui.navigate.to('/'))
            ui.menu_item('Initialization', on_click=lambda: ui.navigate.to('/initialization'))
            ui.menu_item('Add Participant', on_click=lambda: ui.navigate.to('/add_user'))
            with ui.menu_item('View/Edit Participant', auto_close=False):
                with ui.item_section().props('side'):
                    ui.icon('keyboard_arrow_right')
                with ui.menu().props('anchor="top end" self="top start" auto-close'):
                    ui.menu_item("View/Edit Participant Details", on_click=lambda: ui.navigate.to('/view_edit_user'))
                    ui.menu_item("Delete Participant", on_click=lambda: ui.navigate.to('/delete_user'))
            ui.menu_item('Send Test SMS', on_click=lambda: ui.navigate.to('/send_sms'))
            with ui.menu_item('Participant Checks', auto_close=False):
                with ui.item_section().props('side'):
                    ui.icon('keyboard_arrow_right')
                with ui.menu().props('anchor="top end" self="top start" auto-close'):
                    ui.menu_item("Daily Report")
                    ui.menu_item("Check Individual Compliance")
            

def top_bar(page_title: str):
    dark = ui.dark_mode(True)
    
    with ui.row().classes('w-screen items-center no-wrap justify-between'):
        
        with ui.row().classes('justify-start'):
            menu()
            ui.button(icon='home', on_click=lambda: ui.navigate.to('/')).props('flat')
            
        with ui.row().classes('justify-center'):
            ui.label(page_title).classes('text-h5')  
                
        with ui.row().classes('justify-end'):
            ui.switch('Dark Mode').bind_value(dark)