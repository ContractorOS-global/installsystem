from django.shortcuts import render

def wallet_view(request):
    return render(request, "orders/wallet.html")
