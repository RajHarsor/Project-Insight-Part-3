import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from nicegui import ui

from components import top_bar
from src.pages.initialization_page import initialization_page
from src.pages.add_user_page import add_user_page

def root():
    pages = ui.sub_pages()
    pages.add('/initialization', initialization_page)
    pages.add('/add_user', add_user_page)
    pages.add('/', main_page)

def main_page():
    top_bar('Project INSIGHT Part 3 Dashboard')

ui.run(root)
