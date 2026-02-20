from decimal import Decimal
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import InstallationOrder, Company, Delivery


def clamp(v: Decimal, a: Decimal, b: Decimal) -> Decimal:
    """Ограничивает число в диапазоне [a, b]."""
    return max(a, min(b, v))


def recalc_company(company_id: int):
    """
    Пересчитывает рейтинг фирмы по заказам.
    Сейчас рейтинг простой:
    - базово 5.00
    - company_fault ухудшает
    - not_possible/storno ухудшают
    """
    c = Company.objects.filter(id=company_id).first()
    if not c:
        return

    # В MVP считаем по текущим заказам фирмы (можно позже расширить на историю assignments)
    qs = InstallationOrder.objects.filter(current_company_id=company_id)

    total = qs.count()
    finished = qs.filter(status="finished").count()
    company_fault = qs.filter(reason_category="company_fault").count()
    not_possible = qs.filter(status="not_possible").count()
    storno = qs.filter(status="storno").count()

    if total == 0:
        rating = Decimal("5.00")
    else:
        fault_rate = Decimal(company_fault) / Decimal(total)
        fail_rate = Decimal(not_possible + storno) / Decimal(total)
        rating = Decimal("5.00") - (fault_rate * Decimal("3.00")) - (fail_rate * Decimal("2.00"))
        rating = clamp(rating, Decimal("1.00"), Decimal("5.00")).quantize(Decimal("0.01"))

    c.orders_total = total
    c.orders_finished = finished
    c.company_fault_count = company_fault
    c.not_possible_count = not_possible
    c.storno_count = storno
    c.rating = rating
    c.save(update_fields=[
        "orders_total", "orders_finished", "company_fault_count",
        "not_possible_count", "storno_count", "rating"
    ])


@receiver(post_save, sender=InstallationOrder)
def order_saved(sender, instance: InstallationOrder, created, **kwargs):
    # 1) Автоматически создаём объект доставки для каждого заказа
    if created:
        Delivery.objects.get_or_create(order=instance)

    # 2) Пересчитываем рейтинг фирмы
    if instance.current_company_id:
        recalc_company(instance.current_company_id)


@receiver(post_delete, sender=InstallationOrder)
def order_deleted(sender, instance: InstallationOrder, **kwargs):
    if instance.current_company_id:
        recalc_company(instance.current_company_id)
