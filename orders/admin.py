from django.contrib import admin
from .models import Company, Transaction

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "balance_eur")
    search_fields = ("name", "email")
    filter_horizontal = ("users",)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("date", "type", "source", "amount", "order_id", "comment")
    list_filter = ("type", "date")
    search_fields = ("source", "comment")
