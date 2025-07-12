from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.http import Http404
from .models import City
from apps.businesses.models import Business, BusinessType, BusinessSubtype, BusinessPhoto
from apps.employees.models import Employee
from django.db.models import Count
import random
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
import requests

# Create your views here.

def is_mobile(request):
    """
    Определяет, является ли устройство мобильным
    """
    ua = request.META.get('HTTP_USER_AGENT', '').lower()
    
    # Мобильные устройства
    mobile_keywords = [
        'android', 'iphone', 'ipad', 'ipod', 'opera mini', 'iemobile', 
        'mobile', 'blackberry', 'windows phone', 'webos', 'palm'
    ]
    
    # Проверяем наличие мобильных ключевых слов
    is_mobile_device = any(keyword in ua for keyword in mobile_keywords)
    
    # Дополнительная проверка для планшетов (iPad, Android tablets)
    # Планшеты считаем мобильными устройствами
    tablet_keywords = ['ipad', 'tablet', 'android.*tablet']
    is_tablet = any(keyword in ua for keyword in tablet_keywords)
    
    # Проверяем ширину экрана через JavaScript (если доступно)
    # Это будет работать только если JavaScript включен
    viewport_width = request.GET.get('vw')
    if viewport_width:
        try:
            width = int(viewport_width)
            if width <= 768:  # Мобильные устройства обычно имеют ширину <= 768px
                return True
        except ValueError:
            pass
    
    return is_mobile_device or is_tablet

def get_language_from_request(request):
    """
    Определяет язык из запроса (аналогично main_page)
    """
    lang = None
    user = getattr(request, 'user', None)
    
    # 1. Язык из GET-параметра (ручной переключатель)
    lang_param = request.GET.get('lang')
    if lang_param in ['ru', 'ky']:
        lang = lang_param
        # Если пользователь авторизован — сохранить в профиль
        if user and user.is_authenticated:
            if hasattr(user, 'preferred_language') and user.preferred_language != lang_param:
                user.preferred_language = lang_param
                user.save(update_fields=['preferred_language'])
        else:
            # Для гостей — сохранить в сессию
            request.session['preferred_language'] = lang_param
    # 2. Если пользователь авторизован — брать из профиля
    elif user and user.is_authenticated and hasattr(user, 'preferred_language'):
        lang = user.preferred_language
    # 3. Если есть в сессии (для гостей)
    elif request.session.get('preferred_language') in ['ru', 'ky']:
        lang = request.session['preferred_language']
    # 4. Если не авторизован — брать из HTTP_ACCEPT_LANGUAGE
    else:
        accept_lang = request.META.get('HTTP_ACCEPT_LANGUAGE', '').lower()
        if accept_lang.startswith('ky'):
            lang = 'ky'
        elif accept_lang.startswith('ru'):
            lang = 'ru'
        elif 'ky' in accept_lang.split(',')[0]:
            lang = 'ky'
        else:
            lang = 'ru'
    
    return lang

def custom_404(request, exception=None):
    """
    Кастомная страница 404 с поддержкой мультиязычности
    """
    lang = get_language_from_request(request)
    context = {
        'current_language': lang
    }
    template = f'{lang}/404.html'
    return render(request, template, context, status=404)

def custom_500(request):
    """
    Кастомная страница 500 с поддержкой мультиязычности
    """
    lang = get_language_from_request(request)
    context = {
        'current_language': lang
    }
    template = f'{lang}/500.html'
    return render(request, template, context, status=500)

def custom_403(request, exception=None):
    """
    Кастомная страница 403 с поддержкой мультиязычности
    """
    lang = get_language_from_request(request)
    context = {
        'current_language': lang
    }
    template = f'{lang}/403.html'
    return render(request, template, context, status=403)

class DemoDashboardView(TemplateView):
    """Автоматически определяет устройство и показывает соответствующий шаблон"""
    
    def get_template_names(self):
        # Определяем язык из URL
        lang = 'ru'  # по умолчанию русский
        if 'ky' in self.request.path:
            lang = 'ky'
        
        # Определяем тип устройства
        if is_mobile(self.request):
            template_name = f'{lang}/demo_dashboard_mobile.html'
        else:
            template_name = f'{lang}/demo_dashboard.html'
        
        return [template_name]

def main_page(request):
    """
    View function for rendering the main page
    """
    # Язык по умолчанию
    lang = None
    user = getattr(request, 'user', None)
    # 1. Язык из GET-параметра (ручной переключатель)
    lang_param = request.GET.get('lang')
    if lang_param in ['ru', 'ky']:
        lang = lang_param
        # Если пользователь авторизован — сохранить в профиль
        if user and user.is_authenticated:
            if hasattr(user, 'preferred_language') and user.preferred_language != lang_param:
                user.preferred_language = lang_param
                user.save(update_fields=['preferred_language'])
        else:
            # Для гостей — сохранить в сессию
            request.session['preferred_language'] = lang_param
    # 2. Если пользователь авторизован — брать из профиля
    elif user and user.is_authenticated and hasattr(user, 'preferred_language'):
        lang = user.preferred_language
    # 3. Если есть в сессии (для гостей)
    elif request.session.get('preferred_language') in ['ru', 'ky']:
        lang = request.session['preferred_language']
    # 4. Если не авторизован — брать из HTTP_ACCEPT_LANGUAGE
    else:
        accept_lang = request.META.get('HTTP_ACCEPT_LANGUAGE', '').lower()
        if accept_lang.startswith('ky'):
            lang = 'ky'
        elif accept_lang.startswith('ru'):
            lang = 'ru'
        elif 'ky' in accept_lang.split(',')[0]:
            lang = 'ky'
        else:
            lang = 'ru'
    # Все подкатегории для карточек сверху
    all_subcategories = list(BusinessSubtype.objects.values('id', 'name', 'icon'))
    # 5 случайных подкатегорий для секции с бизнесами
    all_ids = list(BusinessSubtype.objects.values_list('id', flat=True))
    random_ids = random.sample(all_ids, min(5, len(all_ids)))
    random_subcategories_qs = BusinessSubtype.objects.filter(id__in=random_ids)
    random_subcategories = []
    for subcat in random_subcategories_qs:
        businesses = Business.objects.filter(subtype=subcat, is_active=True)
        business_list = []
        for b in businesses:
            photo_obj = BusinessPhoto.objects.filter(business=b).first()
            if photo_obj and photo_obj.image:
                image_url = request.build_absolute_uri(photo_obj.image.url)
            else:
                image_url = '/api/placeholder/300/200'
            business_list.append({
                'id': b.id,
                'name': b.name,
                'address': b.address,
                'rating': 9.0,  # Место для будущего рейтинга
                'reviews': 0,   # Место для будущих отзывов
                'price': '$$',  # Место для будущей цены
                'image': image_url
            })
        random_subcategories.append({
            'id': subcat.id,
            'name': subcat.name,
            'icon': subcat.icon,
            'businesses': business_list
        })
    # Лучшие мастера (is_master=True, топ-10 по рейтингу), если нет — любые сотрудники
    best_masters_qs = Employee.objects.filter(is_master=True).order_by('-rating')[:10]
    if not best_masters_qs.exists():
        best_masters_qs = Employee.objects.all().order_by('-rating')[:10]
    masters = []
    for m in best_masters_qs:
        if m.photo:
            photo_url = request.build_absolute_uri(m.photo.url)
        else:
            photo_url = '/api/placeholder/80/80'
        masters.append({
            'name': m.name,
            'position': m.position.name if m.position else '',
            'rating': m.rating,
            'clients': m.clientsCount,
            'photo': photo_url,
        })
    context = {
        'all_subcategories': all_subcategories,
        'random_subcategories': random_subcategories,
        'masters': masters,
        'current_language': lang
    }
    template = f'{lang}/landing.html'
    return render(request, template, context)

def business_photos_api(request, business_id):
    photos = BusinessPhoto.objects.filter(business_id=business_id)
    photo_urls = [request.build_absolute_uri(photo.image.url) for photo in photos if photo.image]
    return JsonResponse({'photos': photo_urls})

def city_list(request):
    cities = list(City.objects.values('id', 'name'))
    return JsonResponse({'cities': cities})

@csrf_exempt
@login_required
def save_city(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        city_id = data.get('city_id')
        if city_id:
            city = City.objects.filter(id=city_id).first()
            if city:
                user = request.user
                user.city = city
                user.save()
                return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)

@csrf_exempt
def send_demo(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        business_type = request.POST.get('business_type')
        comment = request.POST.get('comment', '')

        TELEGRAM_TOKEN = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        TELEGRAM_CHAT_ID = getattr(settings, 'TELEGRAM_ADMIN_CHAT_ID', None)
        if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
            return JsonResponse({'status': 'error', 'message': 'Telegram settings missing'}, status=500)

        message = (
            f"Новая заявка на демо:\n"
            f"Имя: {name}\n"
            f"Телефон: {phone}\n"
            f"Тип бизнеса: {business_type}\n"
            f"Комментарий: {comment}"
        )
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        }
        try:
            requests.post(url, data=data, timeout=5)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)
