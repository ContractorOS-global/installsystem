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

admin.site.register(Company)
admin.site.register(InstallationOrder)
admin.site.register(Delivery)
admin.site.register(PenaltyRule)
admin.site.register(LedgerEntry)
admin.site.register(OrderAssignment)
admin.site.register(OrderDocument)
