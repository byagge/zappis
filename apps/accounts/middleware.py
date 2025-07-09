from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model

class UserActivityMiddleware(MiddlewareMixin):
    def process_request(self, request):
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            ip = self.get_client_ip(request)
            device = request.META.get('HTTP_USER_AGENT', '')[:255]
            now = timezone.now()
            updated = False
            # Обновляем только если что-то изменилось
            if user.last_login_ip != ip:
                user.last_login_ip = ip
                updated = True
            if user.last_login_device != device:
                user.last_login_device = device
                user.last_login_device_time = now
                updated = True
            # Всегда обновляем время последнего входа
            user.last_login_time = now
            updated = True
            if updated:
                UserModel = get_user_model()
                UserModel.objects.filter(pk=user.pk).update(
                    last_login_time=user.last_login_time,
                    last_login_ip=user.last_login_ip,
                    last_login_device=user.last_login_device,
                    last_login_device_time=user.last_login_device_time
                )

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip 