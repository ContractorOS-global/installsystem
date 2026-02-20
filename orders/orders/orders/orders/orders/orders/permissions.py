from .models import Company

def is_dispatcher(user) -> bool:
    """Dispatcher = superuser (полный доступ)."""
    return user.is_superuser

def user_company(user):
    """Возвращает первую компанию, к которой привязан пользователь фирмы."""
    return Company.objects.filter(users=user).first()
