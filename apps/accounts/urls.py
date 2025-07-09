from django.urls import path
from .views import Step1View, Step2View, Step3View
from .views import RegisterPageView, LoginAPIView, VerifyCodeView, ProfileAPIView, ResendCodeView
from django.views.generic import TemplateView
from apps.accounts.views import SignUpPageView, UserSignUpAPIView
from .views import UserLanguageUpdateAPIView

urlpatterns = [
    path('partners/register/', RegisterPageView.as_view(), name='partners-register-page'),
    path('register/step1/', Step1View.as_view(), name='reg-step1'),
    path('register/step2/', Step2View.as_view(), name='reg-step2'),
    path('register/step3/', Step3View.as_view(), name='reg-step3'),
    path('verify-code/', VerifyCodeView.as_view(), name='verify-code'),
    path('resend-code/', ResendCodeView.as_view(), name='resend-code'),
    path('api/login/', LoginAPIView.as_view(), name='login'),
    path('api/profile/', ProfileAPIView.as_view(), name='profile'),
    path('login/', TemplateView.as_view(template_name='accounts/login.html'), name='login-page'),
    path('register/', TemplateView.as_view(template_name='accounts/signup.html'), name='register-page'),
    path('signup/', SignUpPageView.as_view(), name='signup_page'),
    path('api/signup/', UserSignUpAPIView.as_view(), name='signup_api'),
    path('profile/language/', UserLanguageUpdateAPIView.as_view(), name='user-language-update'),
]
