from django.urls import path
from .views import Step1View, Step2View, Step3View
from .views import RegisterPageView, VerifyCodeView, ProfileAPIView, ResendCodeView
from django.views.generic import TemplateView
from apps.accounts.views import SignUpPageView, UserSignUpAPIView, SimpleRegisterAPIView, BusinessTypesAPIView
from .views import UserLanguageUpdateAPIView, CreateSessionAPIView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('partners/register/', RegisterPageView.as_view(), name='partners-register-page'),
    path('register/step1/', Step1View.as_view(), name='reg-step1'),
    path('register/step2/', Step2View.as_view(), name='reg-step2'),
    path('register/step3/', Step3View.as_view(), name='reg-step3'),
    path('verify-code/', VerifyCodeView.as_view(), name='verify-code'),
    path('resend-code/', ResendCodeView.as_view(), name='resend-code'),
    path('api/profile/', ProfileAPIView.as_view(), name='profile'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html', redirect_authenticated_user=True), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('register/', TemplateView.as_view(template_name='accounts/signup.html'), name='register-page'),
    path('signup/', SignUpPageView.as_view(), name='signup_page'),
    path('api/signup/', UserSignUpAPIView.as_view(), name='signup_api'),
    path('api/register/', SimpleRegisterAPIView.as_view(), name='simple-register-api'),
    path('api/business-types/', BusinessTypesAPIView.as_view(), name='business-types-api'),
    path('api/create-session/', CreateSessionAPIView.as_view(), name='create-session'),
    path('profile/language/', UserLanguageUpdateAPIView.as_view(), name='user-language-update'),
]
