from django import forms
from .models import InstallationOrder, Delivery, OrderDocument


class OrderCreateForm(forms.ModelForm):
    """
    Форма создания заказа (пока вручную).
    Позже эти поля будут заполняться из PDF автоматически.
    """
    class Meta:
        model = InstallationOrder
        fields = [
            "order_number", "customer_name", "address", "phone",
            "date", "time_from", "time_to",
            "base_price_eur",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "time_from": forms.TimeInput(attrs={"type": "time"}),
            "time_to": forms.TimeInput(attrs={"type": "time"}),
            "address": forms.Textarea(attrs={"rows": 3}),
        }


class OrderCompanyUpdateForm(forms.ModelForm):
    """
    Форма для фирмы: обновить статус, причину и фото.
    Важно: для not_possible и storno — причина и фото обязательны.
    """
    class Meta:
        model = InstallationOrder
        fields = ["status", "reason_category", "reason_text", "photo"]
        widgets = {"reason_text": forms.Textarea(attrs={"rows": 3})}

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get("status")
        reason_text = (cleaned.get("reason_text") or "").strip()
        photo = cleaned.get("photo")
        has_existing_photo = bool(getattr(self.instance, "photo", None))

        if status in ("not_possible", "storno"):
            if not reason_text:
                raise forms.ValidationError("Для not_possible/storno обязательно reason_text.")
            if not photo and not has_existing_photo:
                raise forms.ValidationError("Для not_possible/storno обязательно фото.")
        return cleaned


class DeliveryForm(forms.ModelForm):
    class Meta:
        model = Delivery
        fields = ["status", "carrier", "tracking_number", "planned_date", "delivered_date", "notes"]
        widgets = {
            "planned_date": forms.DateInput(attrs={"type": "date"}),
            "delivered_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class PdfUploadForm(forms.ModelForm):
    """
    Загрузка PDF заказа в PDF Inbox.
    """
    class Meta:
        model = OrderDocument
        fields = ["source", "file"]
