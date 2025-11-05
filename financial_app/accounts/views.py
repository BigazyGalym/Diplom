# accounts/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from datetime import date
from .models import User, Wallet, Transaction, Budget, Debt
from django.db.models import Sum
from .serializers import UserSerializer, WalletSerializer, TransactionSerializer, BudgetSerializer, DebtSerializer, GoogleLoginSerializer

class GoogleLoginView(APIView):
    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            Wallet.objects.create(user=user, name='Cash', balance=0.00)
            Wallet.objects.create(user=user, name='Card', balance=0.00)
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'User created successfully',
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(email=email, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }, status=status.HTTP_200_OK)
        return Response({'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class FinanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        now = date.today()
        transactions = Transaction.objects.filter(user=user, date__year=now.year, date__month=now.month)
        income = sum(t.amount for t in transactions if t.type == 'income')
        expenses = sum(t.amount for t in transactions if t.type == 'expense')
        categories = transactions.filter(type='expense').values('category').annotate(total=Sum('amount')).order_by('category')
        budgets = Budget.objects.filter(user=user)
        budget_data = []
        total_limit = 0
        total_spent = expenses
        for budget in budgets:
            spent = transactions.filter(type='expense', category=budget.category).aggregate(Sum('amount'))['amount__sum'] or 0
            budget_data.append({
                'category': budget.category,
                'limit': budget.limit,
                'spent': spent
            })
            total_limit += budget.limit
        debts = DebtSerializer(Debt.objects.filter(user=user), many=True).data
        return Response({
            'income': income,
            'wallets': WalletSerializer(Wallet.objects.filter(user=user), many=True).data,
            'expenses': expenses,
            'categories': [{'category': c['category'], 'amount': c['total'] or 0} for c in categories],
            'transactions': TransactionSerializer(transactions, many=True).data,
            'budgets': budget_data,
            'total_limit': total_limit,
            'total_spent': total_spent,
            'debts': debts
        })

class WalletCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WalletSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TransactionCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TransactionSerializer(data=request.data)
        if serializer.is_valid():
            transaction = serializer.save(user=request.user)
            wallet = transaction.wallet
            if transaction.type == 'income':
                wallet.balance += transaction.amount
            else:
                wallet.balance -= transaction.amount
            wallet.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BudgetCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BudgetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DebtCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DebtSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({'message': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user
    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data)
    elif request.method == 'PATCH':
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class HomeView(APIView):
    """Home view"""
    def get(self, request):
        return Response({"message": "Welcome to your dashboard!"})