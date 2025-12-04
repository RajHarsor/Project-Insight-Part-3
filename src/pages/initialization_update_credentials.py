from nicegui import ui
from components import top_bar

print(">>> Loading initialization_update_credentials.py")

@ui.page('/initialization/update_credentials')
def update_credentials():
    print(">>> Entering update_credentials()")
    top_bar('Update Credentials')
    print(">>> Finished update_credentials()")