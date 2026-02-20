from django.contrib import admin
from .models import (
    Company,
    InstallationOrder,
    Delivery,
    PenaltyRule,
    LedgerEntry,
    OrderAssignment,
    OrderDocument,
)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "rating", "balance_eur", "orders_total", "orders_finished")
    filter_horizontal = ("users",)
    ordering = ("-rating", "name")


@admin.register(InstallationOrder)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "customer_name",
        "date",
        "status",
        "current_company",
        "base_price_eur",
        "bonus_pot_eur",
        "taken_from_pool",
    )
    list_filter = ("status", "current_company", "taken_from_pool")
    search_fields = ("order_number", "customer_name")


@admin.register(OrderDocument)
class OrderDocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "source", "status", "filename", "size_bytes", "created_at", "order")
    list_filter = ("source", "status")
    search_fields = ("filename", "sha256")


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ("order", "status", "carrier", "tracking_number", "updated_at")
    list_filter = ("status", "carrier")
    search_fields = ("order__order_number", "tracking_number", "carrier")


@admin.register(PenaltyRule)
class PenaltyRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "hours_before_install_from", "hours_before_install_to", "penalty_eur", "is_active")
    list_filter = ("is_active",)


@admin.register(LedgerEntry)
class LedgerAdmin(admin.ModelAdmin):
    list_display = ("company", "entry_type", "source", "amount_eur", "order", "created_at")
    list_filter = ("entry_type", "source", "company")
    search_fields = ("company__name", "order__order_number", "comment")


@admin.register(OrderAssignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("order", "company", "assigned_at", "unassigned_at", "unassign_reason")
    list_filter = ("company",)
