import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from nicegui import ui

from components import top_bar
from src.pages.initialization_page import initialization_page
from src.pages.initialization_update_credentials import update_credentials
from src.pages.initialization_setup_credentials import setup_credentials

def root():
    pages = ui.sub_pages()
    pages.add('/initialization', initialization_page)
    pages.add('/', main_page)
    pages.add('/initialization/update_credentials', update_credentials)
    pages.add('/initialization/setup_credentials', setup_credentials)

def main_page():
    top_bar('Project INSIGHT Part 3 Dashboard')

ui.run(root)
