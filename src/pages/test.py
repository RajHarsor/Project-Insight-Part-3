from nicegui import ui

@ui.page('/')
def main():
    ui.label('Main Page')
    
    async def go_to_other():
        ui.navigate.to('/other')
    
    ui.button('Go to other', on_click=go_to_other)

@ui.page('/other')
def other():
    ui.label('Other Page')

ui.run()