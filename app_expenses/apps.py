from django.apps import AppConfig


class AppExpensesConfig(AppConfig):
    name = 'app_expenses'

    def ready(self):
        import app_expenses.signals
