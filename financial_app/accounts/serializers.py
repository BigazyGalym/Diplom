# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Wallet, Transaction, Budget, Debt

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'email', 'profile_photo', 'password']
        read_only_fields = ['email']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone=validated_data.get('phone', ''),
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['email'] = self.user.email
        return data

class GoogleLoginSerializer(serializers.Serializer):
    access_token = serializers.CharField()

    def validate(self, attrs):
        from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
        from allauth.socialaccount.providers.oauth2.client import OAuth2Client
        from allauth.socialaccount.models import SocialToken
        from rest_framework_simplejwt.tokens import RefreshToken
        adapter = GoogleOAuth2Adapter()
        client = OAuth2Client(adapter.get_provider().get_app())
        token = attrs['access_token']
        try:
            social_token = SocialToken(token=token)
            sociallogin = adapter.complete_login(
                request=self.context['request'],
                app=social_token.app,
                token=social_token,
            )
            sociallogin.lookup()
            sociallogin.user = sociallogin.account.user or User.objects.get_or_create(email=sociallogin.account.extra_data['email'])[0]
            sociallogin.save(self.context['request'])
            refresh = RefreshToken.for_user(sociallogin.user)
            return {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'email': sociallogin.user.email
            }
        except Exception as e:
            raise serializers.ValidationError(f"Google login failed: {str(e)}")

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id', 'name', 'balance']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'wallet', 'type', 'category', 'amount', 'date']

class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ['id', 'category', 'limit']

class DebtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Debt
        fields = ['id', 'type', 'counterparty', 'amount', 'due_date', 'returned']