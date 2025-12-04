from nicegui import ui
from components import top_bar

print(">>> Loading initialization_setup_credentials.py")

@ui.page('/initialization/setup_credentials')
def setup_credentials():
    print(">>> Entering setup_credentials()")
    top_bar('Setup Credentials')
    print(">>> Finished setup_credentials()")