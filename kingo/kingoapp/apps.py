from django.apps import AppConfig
import atexit

class KingoappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'kingoapp'

    # def ready(self):
    #         from .start_telegram_bot import start_telegram_bot, stop_telegram_bot
    #         start_telegram_bot()
    #         atexit.register(stop_telegram_bot)
