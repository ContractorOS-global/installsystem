from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q
import hashlib


class Company(models.Model):
    """
    Компания (фирма), которая выполняет установки.
    К ней привязываются пользователи (company users).
    Также здесь хранится рейтинг и баланс (кошелёк).
    """
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    users = models.ManyToManyField(User, blank=True, related_name="companies")

    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)
    orders_total = models.PositiveIntegerField(default=0)
    orders_finished = models.PositiveIntegerField(default=0)
    company_fault_count = models.PositiveIntegerField(default=0)
    not_possible_count = models.PositiveIntegerField(default=0)
    storno_count = models.PositiveIntegerField(default=0)

    balance_eur = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.name


class InstallationOrder(models.Model):
    """
    Заказ на установку.
    Основной объект, который назначается фирмам.
    """
    STATUS_CHOICES = [
        ("inbox", "Inbox"),
        ("open_pool", "Open Pool"),
        ("assigned", "Zugewiesen"),
        ("in_progress", "In Arbeit"),
        ("finished", "Fertig"),
        ("not_possible", "Nicht möglich"),
        ("storno", "Storno"),
    ]

    REASON_CATEGORY = [
        ("neutral", "Neutral"),
        ("company_fault", "Company Fault"),
    ]

    order_number = models.CharField(max_length=100, unique=True)
    customer_name = models.CharField(max_length=255)
    address = models.TextField(blank=True, default="")
    phone = models.CharField(max_length=50, blank=True, default="")

    date = models.DateField()
    time_from = models.TimeField()
    time_to = models.TimeField()

    current_company = models.ForeignKey(
        Company, on_delete=models.SET_NULL, null=True, blank=True, related_name="current_orders"
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="inbox")

    reason_category = models.CharField(max_length=20, choices=REASON_CATEGORY, blank=True, null=True)
    reason_text = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to="order_photos/", blank=True, null=True)

    base_price_eur = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bonus_pot_eur = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    taken_from_pool = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_orders"
    )

    def __str__(self):
        return self.order_number


class OrderAssignment(models.Model):
    """
    История назначений заказа фирмам.
    Важно: активное назначение может быть только одно (constraint).
    """
    order = models.ForeignKey(InstallationOrder, on_delete=models.CASCADE, related_name="assignments")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="assignments")

    assigned_at = models.DateTimeField(auto_now_add=True)
    unassigned_at = models.DateTimeField(blank=True, null=True)

    actor_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    unassign_reason = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["order"],
                condition=Q(unassigned_at__isnull=True),
                name="uniq_active_assignment_per_order",
            )
        ]

    @property
    def is_active(self):
        return self.unassigned_at is None


class PenaltyRule(models.Model):
    """
    Правило штрафов при отказе.
    Выбирается по количеству часов до установки.
    """
    name = models.CharField(max_length=200)
    hours_before_install_from = models.PositiveIntegerField()
    hours_before_install_to = models.PositiveIntegerField()
    penalty_eur = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["hours_before_install_from"]

    def __str__(self):
        return f"{self.name}: {self.penalty_eur}€"


class LedgerEntry(models.Model):
    """
    Кошелёк фирмы (журнал операций).
    base_payment - оплата за заказ
    bonus_credit - бонус из общего контейнера
    penalty - штраф при отказе
    """
    TYPE = [
        ("penalty", "Penalty"),
        ("base_payment", "Base Payment"),
        ("bonus_credit", "Bonus Credit"),
        ("manual", "Manual"),
    ]

    SOURCE = [
        ("direct", "Direct"),
        ("open_pool", "Open Pool"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="ledger")
    order = models.ForeignKey(
        InstallationOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name="ledger"
    )

    entry_type = models.CharField(max_length=20, choices=TYPE)
    source = models.CharField(max_length=20, choices=SOURCE, default="direct")
    amount_eur = models.DecimalField(max_digits=10, decimal_places=2)

    comment = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Delivery(models.Model):
    """
    Модуль доставки (1:1 с заказом).
    """
    DELIVERY_STATUS = [
        ("none", "Нет"),
        ("planned", "Запланировано"),
        ("sent", "Отправлено"),
        ("delivered", "Доставлено"),
        ("failed", "Не удалось"),
    ]

    order = models.OneToOneField(InstallationOrder, on_delete=models.CASCADE, related_name="delivery")
    status = models.CharField(max_length=20, choices=DELIVERY_STATUS, default="planned")

    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    carrier = models.CharField(max_length=100, blank=True, null=True)

    planned_date = models.DateField(blank=True, null=True)
    delivered_date = models.DateField(blank=True, null=True)

    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Delivery for {self.order.order_number}"


class OrderDocument(models.Model):
    """
    PDF-документ, содержащий заказ.
    Сейчас НЕ парсим, только сохраняем и показываем фирмам.
    Позже парсер будет читать этот PDF и заполнять поля автоматически.
    """
    SOURCE = [
        ("manual", "Manual Upload"),
        ("email", "Email Attachment"),
        ("ikea", "IKEA"),
        ("other", "Other"),
    ]

    status = models.CharField(
        max_length=20,
        choices=[("new", "New"), ("linked", "Linked")],
        default="new",
        db_index=True,
    )
    source = models.CharField(max_length=20, choices=SOURCE, default="manual")

    file = models.FileField(upload_to="order_pdfs/")
    filename = models.CharField(max_length=255, blank=True, default="")
    size_bytes = models.PositiveIntegerField(default=0)

    sha256 = models.CharField(max_length=64, unique=True, db_index=True)

    order = models.OneToOneField(
        InstallationOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_pdf",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def compute_sha256(self):
        h = hashlib.sha256()
        for chunk in self.file.chunks():
            h.update(chunk)
        return h.hexdigest()

    def save(self, *args, **kwargs):
        if self.file:
            try:
                self.size_bytes = self.file.size
            except Exception:
                pass
            if not self.filename:
                self.filename = (getattr(self.file, "name", "") or "")[-255:]
            if not self.sha256:
                self.sha256 = self.compute_sha256()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.filename or 'PDF'} ({self.status})"
