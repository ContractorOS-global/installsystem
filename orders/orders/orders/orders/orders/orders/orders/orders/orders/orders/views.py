from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q

from .models import InstallationOrder, Company, LedgerEntry, Delivery, OrderDocument
from .permissions import is_dispatcher, user_company
from .forms import OrderCreateForm, OrderCompanyUpdateForm, DeliveryForm, PdfUploadForm
from .services import assign_order, take_from_open_pool, company_reject_order, finish_order_and_pay


def home(request):
    return redirect("order_list")


def user_login(request):
    if request.user.is_authenticated:
        return redirect("order_list")

    if request.method == "POST":
        u = request.POST.get("username", "").strip()
        p = request.POST.get("password", "").strip()
        user = authenticate(request, username=u, password=p)
        if user:
            login(request, user)
            return redirect("order_list")
        messages.error(request, "Неверный логин или пароль.")

    return render(request, "orders/login.html")


def user_logout(request):
    logout(request)
    return redirect("login")


@login_required
def order_list(request):
    """
    Dispatcher видит все заказы.
    Фирма видит только свои.
    """
    qs = InstallationOrder.objects.select_related("current_company").order_by("-created_at")

    if not is_dispatcher(request.user):
        c = user_company(request.user)
        qs = qs.filter(current_company=c) if c else qs.none()

    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    if q:
        qs = qs.filter(Q(order_number__icontains=q) | Q(customer_name__icontains=q))
    if status:
        qs = qs.filter(status=status)

    return render(request, "orders/order_list.html", {
        "orders": qs[:300],
        "q": q,
        "status": status,
        "status_choices": InstallationOrder.STATUS_CHOICES,
        "is_dispatcher": is_dispatcher(request.user),
    })


@login_required
def order_detail(request, pk):
    """
    Карточка заказа. Фирма должна видеть PDF и фото.
    """
    order = get_object_or_404(InstallationOrder.objects.select_related("current_company"), pk=pk)

    if not is_dispatcher(request.user):
        c = user_company(request.user)
        if not c or order.current_company_id != c.id:
            messages.error(request, "Нет доступа к этому заказу.")
            return redirect("my_orders")

    return render(request, "orders/order_detail.html", {
        "order": order,
        "is_dispatcher": is_dispatcher(request.user),
        "company": user_company(request.user),
    })


@login_required
def order_edit_company(request, pk):
    """
    Форма для фирмы: обновить статус, причину, фото.
    """
    order = get_object_or_404(InstallationOrder, pk=pk)
    c = user_company(request.user)
    if not c or order.current_company_id != c.id:
        messages.error(request, "Нет доступа.")
        return redirect("my_orders")

    if request.method == "POST":
        form = OrderCompanyUpdateForm(request.POST, request.FILES, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, "Обновлено.")
            return redirect("order_detail", pk=order.pk)
    else:
        form = OrderCompanyUpdateForm(instance=order)

    return render(request, "orders/order_form.html", {"form": form, "order": order})


# ---------------- PDF INBOX ----------------

@login_required
def pdf_inbox(request):
    """
    Контейнер новых PDF заказов.
    Доступ: только dispatcher.
    """
    if not is_dispatcher(request.user):
        return redirect("my_orders")

    docs = OrderDocument.objects.filter(status="new").order_by("-created_at")[:300]
    return render(request, "orders/pdf_inbox.html", {"docs": docs})


@login_required
def pdf_upload(request):
    """
    Загрузка PDF заказа в контейнер.
    Дубликаты отсеиваются по sha256 (unique).
    Доступ: только dispatcher.
    """
    if not is_dispatcher(request.user):
        return redirect("my_orders")

    if request.method == "POST":
        form = PdfUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "PDF загружен в контейнер.")
                return redirect("pdf_inbox")
            except Exception as e:
                messages.error(request, f"Не удалось сохранить PDF (возможно дубль): {e}")
    else:
        form = PdfUploadForm()

    return render(request, "orders/pdf_upload.html", {"form": form})


@login_required
def pdf_create_order(request, doc_id):
    """
    Создание InstallationOrder из PDF (пока вручную).
    После создания связываем PDF с заказом и убираем из контейнера.
    """
    if not is_dispatcher(request.user):
        return redirect("my_orders")

    doc = get_object_or_404(OrderDocument, pk=doc_id, status="new")

    if request.method == "POST":
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.status = "inbox"
            order.created_by = request.user
            order.save()

            doc.order = order
            doc.status = "linked"
            doc.save(update_fields=["order", "status"])

            messages.success(request, "Заказ создан и PDF привязан.")
            return redirect("order_detail", pk=order.id)
    else:
        form = OrderCreateForm(initial={
            "order_number": f"PDF-{doc.id}",
            "customer_name": "Импорт из PDF",
            "base_price_eur": 100,
        })

    return render(request, "orders/pdf_create_order.html", {"doc": doc, "form": form})


# ---------------- POOL / MY ORDERS / WALLET ----------------

@login_required
def pool(request):
    """
    Общий контейнер. Любая фирма может взять заказ.
    """
    c = user_company(request.user)
    if not c:
        messages.error(request, "Вы не привязаны к фирме.")
        return redirect("order_list")

    qs = InstallationOrder.objects.filter(status="open_pool").order_by("date", "time_from")[:300]
    return render(request, "orders/pool.html", {"orders": qs, "company": c})


@login_required
def pool_take(request, pk):
    c = user_company(request.user)
    if not c:
        return redirect("pool")
    try:
        take_from_open_pool(pk, c.id, actor_user=request.user)
        messages.success(request, "Вы взяли заказ.")
    except Exception as e:
        messages.error(request, str(e))
    return redirect("my_orders")


@login_required
def my_orders(request):
    """
    Заказы текущей фирмы.
    """
    c = user_company(request.user)
    if not c:
        messages.error(request, "Вы не привязаны к фирме.")
        return redirect("order_list")

    qs = InstallationOrder.objects.filter(current_company=c).order_by("date", "time_from")[:300]
    return render(request, "orders/my_orders.html", {"orders": qs, "company": c})


@login_required
def reject_order(request, pk):
    """
    Отказ фирмы -> штраф -> заказ уходит в open_pool.
    """
    c = user_company(request.user)
    if not c:
        return redirect("my_orders")

    reason = (request.POST.get("reason", "") or "").strip()[:200]
    if not reason:
        reason = "No reason"

    try:
        company_reject_order(pk, c.id, reason=reason, actor_user=request.user)
        messages.success(request, "Вы отказались от заказа. Он ушёл в общий контейнер.")
    except Exception as e:
        messages.error(request, str(e))
    return redirect("my_orders")


@login_required
def finish_order(request, pk):
    """
    Завершение заказа -> начисление base + bonus.
    """
    c = user_company(request.user)
    if not c:
        return redirect("my_orders")
    try:
        finish_order_and_pay(pk, c.id)
        messages.success(request, "Заказ завершён. Оплата/бонус начислены в кошелёк.")
    except Exception as e:
        messages.error(request, str(e))
    return redirect("order_detail", pk=pk)


@login_required
def wallet(request):
    """
    Кошелёк фирмы: баланс и операции.
    """
    c = user_company(request.user)
    if not c:
        messages.error(request, "Вы не привязаны к фирме.")
        return redirect("order_list")

    entries = LedgerEntry.objects.filter(company=c).order_by("-created_at")[:400]
    return render(request, "orders/wallet.html", {"company": c, "entries": entries})


# ---------------- DELIVERY ----------------

@login_required
def delivery_list(request):
    qs = Delivery.objects.select_related("order", "order__current_company").order_by("-updated_at")[:300]
    if not is_dispatcher(request.user):
        c = user_company(request.user)
        qs = qs.filter(order__current_company=c) if c else qs.none()
    return render(request, "orders/delivery_list.html", {"deliveries": qs})


@login_required
def delivery_edit(request, order_pk):
    order = get_object_or_404(InstallationOrder, pk=order_pk)
    if not is_dispatcher(request.user):
        c = user_company(request.user)
        if not c or order.current_company_id != c.id:
            messages.error(request, "Нет доступа.")
            return redirect("my_orders")

    delivery = getattr(order, "delivery", None)
    if not delivery:
        Delivery.objects.create(order=order)
        delivery = order.delivery

    if request.method == "POST":
        form = DeliveryForm(request.POST, instance=delivery)
        if form.is_valid():
            form.save()
            messages.success(request, "Доставка обновлена.")
            return redirect("order_detail", pk=order.pk)
    else:
        form = DeliveryForm(instance=delivery)

    return render(request, "orders/delivery_form.html", {"order": order, "form": form})


@login_required
def company_ratings(request):
    companies = Company.objects.order_by("-rating", "name")
    return render(request, "orders/company_ratings.html", {"companies": companies})


# ---------------- INBOX placeholder ----------------

@login_required
def inbox(request):
    """
    Заглушка под email inbox (на будущее).
    Сейчас используем PDF Inbox.
    """
    if not is_dispatcher(request.user):
        return redirect("my_orders")
    messages.info(request, "Email Inbox будет подключен позже. Сейчас используйте PDF Inbox.")
    return redirect("pdf_inbox")
