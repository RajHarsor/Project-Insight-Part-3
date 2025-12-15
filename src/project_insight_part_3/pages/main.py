from nicegui import ui

from .components import top_bar
from .initialization_page import initialization_page
from .add_user_page import add_user_page
from .confirm_add_user_page import confirm_add_user_page
from .view_edit_user_page import view_edit_user_page
from .delete_user_page import delete_user_page
from .send_sms_page import send_sms_page


def register_pages() -> None:
    ui.page('/')(main_page)
    ui.page('/initialization')(initialization_page)
    ui.page('/add_user')(add_user_page)
    ui.page('/confirm_add_user')(confirm_add_user_page)
    ui.page('/view_edit_user')(view_edit_user_page)
    ui.page('/delete_user')(delete_user_page)
    ui.page('/send_sms')(send_sms_page)


def main_page():
    top_bar('Project INSIGHT Part 3 Dashboard')

    with ui.row().classes('w-full justify-center'):
        with ui.column().classes('w-100'):
            ui.label('Participant Progress Overview').classes('text-lg font-bold mb-5')
        with ui.column().classes('w-100'):
            ui.label('Recent Activities').classes('text-lg font-bold mb-5')
        with ui.column().classes('w-100 outline outline-cyan-500 outline-offset-10 rounded-lg'):
            ui.label('Useful Links').classes('text-lg font-bold mb-5')

            ui.link('Project INSIGHT Website', 'https://projectinsighthealth.org/')
            ui.link('Project INSIGHT Google Drive','https://drive.google.com/drive/folders/1dHpQ_wOzshmQXk1aQO-cH4GCdB1QiGup?usp=drive_link')
            ui.link('Qualtrics', 'https://rowan.qualtrics.com/')
            ui.link('Project Repository', 'https://github.com/RajHarsor/Project-Insight-Part-3')
            ui.link('AWS Login', 'https://rowan.awsapps.com/start/')
            ui.link('NiceGUI Documentation', 'https://nicegui.io/documentation')
            ui.link('Tailwind CSS Documentation', 'https://tailwindcss.com/docs')


def main() -> None:
    register_pages()
    ui.run(port=8081, reload=False)


if __name__ in {"__main__", "__mp_main__"}:
    main()
