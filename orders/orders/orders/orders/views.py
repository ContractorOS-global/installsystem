from django.shortcuts import render
from .models import Order


def wallet_view(request):
    orders = Order.objects.all().order_by('-created_at')

    context = {
        'orders': orders
    }

    return render(request, 'orders/wallet.html', context)
