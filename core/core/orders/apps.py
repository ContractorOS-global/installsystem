from django.apps import AppConfig

class OrdersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "orders"

    def ready(self):
        # подключаем signals (авто-обновление рейтинга/создание delivery)
        from . import signals  # noqa
