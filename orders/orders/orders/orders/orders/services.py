from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from .models import (
    InstallationOrder,
    OrderAssignment,
    Company,
    PenaltyRule,
    LedgerEntry,
)


def _hours_to_install(order: InstallationOrder) -> int:
    """
    Считает сколько часов осталось до времени установки (date + time_from).
    Используется для выбора штрафа.
    """
    dt_install = timezone.make_aware(
        timezone.datetime.combine(order.date, order.time_from),
        timezone.get_current_timezone()
    )
    delta = dt_install - timezone.now()
    return max(0, int(delta.total_seconds() // 3600))


def _get_penalty_amount(order: InstallationOrder) -> Decimal:
    """
    Выбирает штраф по таблице PenaltyRule в зависимости от часов до установки.
    """
    h = _hours_to_install(order)
    rule = (PenaltyRule.objects
            .filter(
                is_active=True,
                hours_before_install_from__lte=h,
                hours_before_install_to__gte=h
            )
            .order_by("hours_before_install_from")
            .first())
    return rule.penalty_eur if rule else Decimal("0.00")


@transaction.atomic
def assign_order(order_id: int, company_id: int, actor_user=None):
    """
    Диспетчер назначает заказ фирме.
    Гарантия: активное назначение только одно (constraint + select_for_update).
    """
    order = InstallationOrder.objects.select_for_update().get(id=order_id)
    company = Company.objects.get(id=company_id)

    if order.status not in ("inbox", "open_pool"):
        raise ValueError("Этот заказ нельзя назначить в текущем статусе.")

    if OrderAssignment.objects.filter(order=order, unassigned_at__isnull=True).exists():
        raise ValueError("Заказ уже назначен другой фирме.")

    OrderAssignment.objects.create(order=order, company=company, actor_user=actor_user)

    order.current_company = company
    order.status = "assigned"
    order.save(update_fields=["current_company", "status", "updated_at"])


@transaction.atomic
def company_reject_order(order_id: int, company_id: int, reason: str, actor_user=None):
    """
    Фирма отказывается от заказа:
    - закрываем активное назначение
    - списываем штраф (PenaltyRule) из баланса фирмы
    - увеличиваем bonus_pot_eur у заказа
    - переносим заказ в общий контейнер (open_pool)
    """
    order = InstallationOrder.objects.select_for_update().get(id=order_id)

    active = (OrderAssignment.objects
              .select_for_update()
              .filter(order=order, unassigned_at__isnull=True)
              .first())

    if not active or active.company_id != company_id:
        raise ValueError("Нельзя отказаться: заказ не принадлежит этой фирме.")

    if order.status == "finished":
        raise ValueError("Нельзя отказаться: заказ уже завершён.")

    penalty = _get_penalty_amount(order)

    active.unassigned_at = timezone.now()
    active.unassign_reason = reason
    active.actor_user = actor_user
    active.save(update_fields=["unassigned_at", "unassign_reason", "actor_user"])

    if penalty > 0:
        comp = Company.objects.select_for_update().get(id=company_id)
        comp.balance_eur = comp.balance_eur - penalty
        comp.save(update_fields=["balance_eur"])

        LedgerEntry.objects.create(
            company=comp,
            order=order,
            entry_type="penalty",
            source="direct",
            amount_eur=Decimal("0.00") - penalty,
            comment=f"Отказ от заказа {order.order_number}. Причина: {reason}",
        )

        order.bonus_pot_eur = order.bonus_pot_eur + penalty

    order.current_company = None
    order.status = "open_pool"
    order.save(update_fields=["current_company", "status", "bonus_pot_eur", "updated_at"])


@transaction.atomic
def take_from_open_pool(order_id: int, company_id: int, actor_user=None):
    """
    Фирма берёт заказ из общего контейнера.
    Гарантия: одновременно взять может только одна фирма.
    """
    order = InstallationOrder.objects.select_for_update().get(id=order_id)

    if order.status != "open_pool":
        raise ValueError("Этот заказ уже недоступен в общем контейнере.")

    if OrderAssignment.objects.filter(order=order, unassigned_at__isnull=True).exists():
        raise ValueError("Заказ уже назначен.")

    company = Company.objects.get(id=company_id)
    OrderAssignment.objects.create(order=order, company=company, actor_user=actor_user)

    order.current_company = company
    order.status = "assigned"
    order.taken_from_pool = True
    order.save(update_fields=["current_company", "status", "taken_from_pool", "updated_at"])


@transaction.atomic
def finish_order_and_pay(order_id: int, actor_company_id: int):
    """
    Фирма завершает заказ:
    - статус -> finished
    - начисляем base_price_eur
