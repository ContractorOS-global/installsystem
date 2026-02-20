from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),

    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),

    path("orders/", views.order_list, name="order_list"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),
    path("orders/<int:pk>/edit-company/", views.order_edit_company, name="order_edit_company"),

    path("pool/", views.pool, name="pool"),
    path("pool/<int:pk>/take/", views.pool_take, name="pool_take"),

    path("my-orders/", views.my_orders, name="my_orders"),
    path("orders/<int:pk>/reject/", views.reject_order, name="reject_order"),
    path("orders/<int:pk>/finish/", views.finish_order, name="finish_order"),

    path("wallet/", views.wallet, name="wallet"),

    path("deliveries/", views.delivery_list, name="delivery_list"),
    path("orders/<int:order_pk>/delivery/", views.delivery_edit, name="delivery_edit"),

    path("companies/ratings/", views.company_ratings, name="company_ratings"),

    # PDF Inbox
    path("pdf-inbox/", views.pdf_inbox, name="pdf_inbox"),
    path("pdf-upload/", views.pdf_upload, name="pdf_upload"),
    path("pdf-inbox/<int:doc_id>/create-order/", views.pdf_create_order, name="pdf_create_order"),

    # Inbox (в будущем для email, но сейчас можно не использовать)
    path("inbox/", views.inbox, name="inbox"),
]
