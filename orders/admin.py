from django.contrib import admin
from .models import Company, Transaction


# -----------------------
# COMPANY (Фирмы)
# -----------------------
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "email",
        "balance_eur",
    )

    search_fields = (
        "name",
        "email",
    )

    filter_horizontal = ("users",)


# -----------------------
# TRANSACTIONS (Кошелек)
# -----------------------
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "date",
        "type",
        "source",
        "amount",
        "order_id",
    )

    list_filter = (
        "type",
        "source",
    )

    search_fields = (
        "source",
        "comment",
    )
