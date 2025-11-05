# accounts/urls.py
from django.urls import path
from .views import (
    RegisterView, LoginView, FinanceView,
    WalletCreateView, TransactionCreateView,
    LogoutView, GoogleLoginView, user_profile,
    BudgetCreateView, DebtCreateView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('finance/', FinanceView.as_view(), name='finance'),
    path('wallet/', WalletCreateView.as_view(), name='wallet_create'),
    path('transaction/', TransactionCreateView.as_view(), name='transaction_create'),
    path('budget/', BudgetCreateView.as_view(), name='budget_create'),
    path('debt/', DebtCreateView.as_view(), name='debt_create'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('google-login/', GoogleLoginView.as_view(), name='google_login'),
    path('user/', user_profile),
]