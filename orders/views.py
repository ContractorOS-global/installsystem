from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Company, Transaction


@login_required
def wallet_view(request):
    """
    Фирма видит только СВОЙ кошелёк.
    Определяем фирму по связи Company.users <-> request.user
    """
    company = Company.objects.filter(users=request.user).first()

    # Если пользователь ни к какой фирме не привязан
    if not company:
        # Админ может управлять фирмами через /admin/
        if request.user.is_superuser:
            return redirect("/admin/")
        # Обычному пользователю покажем простое сообщение
        return render(request, "orders/wallet.html", {
            "company": None,
            "balance": 0,
            "transactions": [],
            "message": "Ваша учетная запись не привязана ни к одной фирме. Обратитесь к администратору."
        })

    # Транзакции (пока без привязки к компании в модели Transaction — показываем все)
    # Если позже добавим ForeignKey на Company, тут легко отфильтруем.
    transactions = Transaction.objects.all().order_by("-date")[:200]

    return render(request, "orders/wallet.html", {
        "company": company,
        "balance": company.balance_eur,
        "transactions": transactions,
        "message": ""
    })
