import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from nicegui import ui

from components import top_bar
from src.pages.initialization_page import initialization_page
from src.pages.add_user_page import add_user_page
from src.pages.confirm_add_user_page import confirm_add_user_page
from src.pages.view_edit_user_page import view_edit_user_page
from src.pages.delete_user_page import delete_user_page
from src.pages.send_sms_page import send_sms_page

def root():
    pages = ui.sub_pages()
    pages.add('/initialization', initialization_page)
    pages.add('/add_user', add_user_page)
    pages.add('/confirm_add_user', confirm_add_user_page)
    pages.add('/view_edit_user', view_edit_user_page)
    pages.add('/delete_user', delete_user_page)
    pages.add('/send_sms', send_sms_page)
    pages.add('/', main_page)

def main_page():
    top_bar('Project INSIGHT Part 3 Dashboard')
    
    with ui.row().classes('w-full justify-center'):
        with ui.column().classes('w-100'):
            ui.label('Participant Progress Overview').classes('text-lg font-bold mb-5')
            # Placeholder for participant progress overview content
        with ui.column().classes('w-100'):
            ui.label('Recent Activities').classes('text-lg font-bold mb-5')
            # Placeholder for recent activities content
        with ui.column().classes('w-100 outline outline-cyan-500 outline-offset-4 rounded-lg'):
            ui.label('Useful Links').classes('text-lg font-bold mb-5')
            
            ui.link('Project INSIGHT Website', 'https://projectinsighthealth.org/')
            ui.link('Project INSIGHT Google Drive', 'https://drive.google.com/drive/folders/1dHpQ_wOzshmQXk1aQO-cH4GCdB1QiGup?usp=drive_link')
            ui.link('Qualtrics', 'https://rowan.qualtrics.com/')
            ui.link('Project Repository', 'https://github.com/RajHarsor/Project-Insight-Part-3')
            ui.link('AWS Login', 'https://rowan.awsapps.com/start/')
            ui.link('NiceGUI Documentation', 'https://nicegui.io/documentation')
            ui.link('Tailwind CSS Documentation', 'https://tailwindcss.com/docs')

ui.run(root, port=8081)
