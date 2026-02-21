from django.db import models


class Transaction(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=50)
    source = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    order_id = models.IntegerField(null=True, blank=True)
    comment = models.TextField(blank=True)

    def __str__(self):
        return f"{self.type} - {self.amount}€"
