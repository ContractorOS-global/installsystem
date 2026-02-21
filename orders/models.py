from django.db import models
from django.contrib.auth.models import User


class Company(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)

    users = models.ManyToManyField(User, blank=True)

    balance_eur = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    def __str__(self):
        return self.name


class Transaction(models.Model):
    date = models.DateTimeField(auto_now_add=True)

    type = models.CharField(max_length=50)
    source = models.CharField(max_length=255)

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    order_id = models.IntegerField(null=True, blank=True)
    comment = models.TextField(blank=True)

    def __str__(self):
        return f"{self.type} - {self.amount}€"
