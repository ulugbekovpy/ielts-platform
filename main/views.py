from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from django.utils import timezone
from .models import IeltsUser, UserStreak, MockResult
from materials.models import ReadingResult, ReadingTest
from django.contrib import messages
from django.db.models import Max, Avg, Count
from datetime import timedelta
from django.template.loader import render_to_string
import json 
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def homepage(request):
    return render(request, 'index.html')

def custom_page_not_found(request, exception):
    return render(request, '404.html', status=404)

def oferta(request):
    return render(request, 'oferta.html')

def logout_view(request):
    request.session.flush()
    return redirect("login")

def register_view(request):
    if request.method == "POST":
        fullname = request.POST.get("fullname", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()

        if IeltsUser.objects.filter(email=email).exists():
            return render(
                request,
                "register.html",
                {"error": "Bu email manzili allaqachon ro'yxatdan o'tgan"},
            )

        hashed_password = make_password(password)

        user = IeltsUser.objects.create(
            email=email, first_name=fullname, password=hashed_password
        )

        otp = user.generate_otp()
        request.session["verification_email"] = email

        context = {
            'otp_1': otp[0],
            'otp_2': otp[1],
            'otp_3': otp[2],
            'otp_4': otp[3],
        }

        html_message = render_to_string('otp_email.html', context)
        plain_message = f"Sizning tasdiqlash kodingiz: {otp}"

        send_mail(
            subject="Tasdiqlash kodi | IELTSPRO",
            message=plain_message,
            from_email="bekovic09@gmail.com",
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )

        return redirect("email_confirmation")

    return render(request, "register.html")


def email_confirmation_view(request):
    email = request.session.get("verification_email")
    if not email:
        return redirect("register")

    try:
        user = IeltsUser.objects.get(email=email)
    except IeltsUser.DoesNotExist:
        return redirect("register")

    if request.method == "POST":
        otp_1 = request.POST.get("otp_1", "")
        otp_2 = request.POST.get("otp_2", "")
        otp_3 = request.POST.get("otp_3", "")
        otp_4 = request.POST.get("otp_4", "")

        input_otp = f"{otp_1}{otp_2}{otp_3}{otp_4}"

        if user.otp_code == input_otp:
            time_diff = timezone.now() - user.otp_created_at
            if time_diff.total_seconds() > 300:
                return render(
                    request,
                    "email-confirmation.html",
                    {"email": email, "error": "Kodning amal qilish muddati tugagan"},
                )

            user.is_verified = True
            user.otp_code = None
            user.otp_created_at = None
            user.save()

            request.session["user_id"] = user.id
            if "verification_email" in request.session:
                del request.session["verification_email"]

            return redirect("plans")
        else:
            return render(
                request,
                "email-confirmation.html",
                {"email": email, "error": "Noto'g'ri kod kiritildi"},
            )

    return render(request, "email-confirmation.html", {"email": email})

def login_view(request):
    if request.session.get('user_id'):
        return redirect('dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        try:
            user = IeltsUser.objects.get(email=email)
            if check_password(password, user.password) or user.password == password:
                
                if not user.is_verified:
                    request.session['verification_email'] = user.email
                    messages.warning(request, "Iltimos, avval elektron pochtangizni tasdiqlang!")
                    return redirect('email_confirmation') 

                request.session['user_id'] = user.id
                return redirect('dashboard')
            else:
                messages.error(request, "Parol noto'g'ri!")
        except IeltsUser.DoesNotExist:
            messages.error(request, "Bunday email bilan foydalanuvchi topilmadi!")

    return render(request, "login.html")


from materials.models import ReadingResult, ReadingTest, ListeningTest, ListeningResult # <-- Добавили Listening
from django.db.models import Max, Avg, Count

# Обновленная функция dashboard:
def dashboard(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    try:
        user = IeltsUser.objects.get(id=user_id)
    except IeltsUser.DoesNotExist:
        return redirect("login")

    today = timezone.now().date()

    # 1. ОБРАБОТКА СТРИКА
    streak_obj, created = UserStreak.objects.get_or_create(user=user)
    if not created:
        last_active = streak_obj.last_activity_date
        if last_active < today:
            if last_active == today - timedelta(days=1):
                streak_obj.current_streak += 1
                if streak_obj.current_streak > streak_obj.longest_streak:
                    streak_obj.longest_streak = streak_obj.current_streak
            else:
                streak_obj.current_streak = 1
            streak_obj.save()

    # 2. ОПРЕДЕЛЕНИЕ ЗАДАНИЙ НА СЕГОДНЯ (READING)
    all_reading_tests = ReadingTest.objects.all().order_by('id')
    day_of_year = timezone.now().timetuple().tm_yday
    total_reading = all_reading_tests.count()
    
    reading_today = None
    reading_is_completed = False
    reading_url = "/materials/reading/"

    if total_reading > 0:
        active_reading_index = day_of_year % total_reading
        reading_today = all_reading_tests[active_reading_index]
        reading_is_completed = ReadingResult.objects.filter(
            user=user, 
            test=reading_today,
            submitted_at__date=today
        ).exists()
        if not reading_is_completed:
            reading_url = f"/materials/reading/test/{reading_today.id}/"

    # ====================================================================
    # 2.1 ДИНАМИЧЕСКАЯ ОБРАБОТКА LISTENING ДЛЯ ПЛАНА НА ДЕНЬ (NEW)
    # ====================================================================
    all_listening_tests = ListeningTest.objects.all().order_by('id')
    total_listening = all_listening_tests.count()
    
    listening_today = None
    listening_is_completed = False
    listening_url = "/materials/listening/"

    if total_listening > 0:
        active_listening_index = day_of_year % total_listening
        listening_today = all_listening_tests[active_listening_index]
        # Проверяем, сдал ли его студент сегодня
        listening_is_completed = ListeningResult.objects.filter(
            user=user,
            test=listening_today,
            submitted_at__date=today
        ).exists()
        # Если не сдал — кнопка «Boshlash» ведет прямо внутрь теста
        if not listening_is_completed:
            listening_url = f"/materials/listening/test/{listening_today.id}/"

    # Контролируемый ежедневный план в правой части экрана[cite: 13]
    modules_list = [
        {
            'name': reading_today.title if reading_today else "Daily Reading Passage",
            'type': 'reading',
            'url': reading_url,
            'status': 'completed' if reading_is_completed else 'pending',
            'icon': '📕'
        },
        {
            'name': listening_today.title if listening_today else "Daily Listening Challenge",
            'type': 'listening',
            'url': listening_url, # <-- Передаем динамический URL вместо заглушки[cite: 13]
            'status': 'completed' if listening_is_completed else 'pending', # <-- Динамический статус[cite: 13]
            'icon': '🎧'
        },
        {
            'name': 'Daily Essay Evaluation',
            'type': 'writing',
            'url': '/materials/writing/',   
            'status': 'pending',
            'icon': '📝'
        }
    ]

    # 3. ИСТОРИЯ БАЛЛОВ (MOCK HISTORY)[cite: 13]
    mock_results = MockResult.objects.filter(user=user)
    latest_score = "0.0"
    best_score = "0.0"
    overall_band_float = 0.0

    if mock_results.exists():
        latest_score = mock_results.first().overall_band
        best_score = mock_results.aggregate(max_score=Max('overall_band'))['max_score']
        overall_band_float = float(latest_score)
    else:
        latest_score = "—"
        best_score = "—"

    target_band = getattr(user, 'want_result', 7.5)
    bands_to_close = max(0.0, float(target_band) - overall_band_float)

    # 4. ТАБЛИЦА ЛИДЕРОВ[cite: 13]
    all_users = IeltsUser.objects.all()
    raw_leaderboard = []
    current_user_has_scores = False
    current_user_data = None

    for u in all_users:
        user_best = MockResult.objects.filter(user=u).aggregate(max_b=Max('overall_band'))['max_b']
        display_name = u.first_name if u.first_name else u.email.split('@')[0]
        is_me = (u.id == user.id)

        if user_best is not None:
            if is_me:
                current_user_has_scores = True
            
            raw_leaderboard.append({
                'user_id': u.id,
                'name': display_name,
                'avatar_letter': display_name[0].upper() if display_name else "U",
                'band_float': float(user_best),
                'band': f"{float(user_best):.1f}",
                'is_current_user': is_me
            })
        elif is_me:
            current_user_data = {
                'user_id': u.id,
                'name': display_name,
                'avatar_letter': display_name[0].upper() if display_name else "U",
                'band': "—",
                'is_current_user': True,
                'rank': "—"
            }

    raw_leaderboard.sort(key=lambda x: x['band_float'], reverse=True)

    leaderboard_data = []
    for index, item in enumerate(raw_leaderboard, start=1):
        item['rank'] = index
        leaderboard_data.append(item)

    leaderboard_data = leaderboard_data[:5]
    show_footer_user = not current_user_has_scores and current_user_data is not None

    # 5. ДИНАМИЧЕСКИЙ РАСЧЕТ ДАННЫХ ДЛЯ SKILL MATRIX[cite: 13]
    user_reading_results = ReadingResult.objects.filter(user=user)
    reading_stats = user_reading_results.aggregate(avg_band=Avg('band'))
    real_reading_score = round(reading_stats['avg_band'], 1) if reading_stats['avg_band'] else 0.0
    reading_percentage = int((real_reading_score / 9.0) * 100) if real_reading_score > 0 else 0

    # ====================================================================
    # 5.1 РАСЧЕТ ДАННЫХ ДЛЯ LISTENING В SKILL MATRIX (NEW)
    # ====================================================================
    user_listening_results = ListeningResult.objects.filter(user=user)
    listening_stats = user_listening_results.aggregate(avg_band=Avg('band'))
    real_listening_score = round(listening_stats['avg_band'], 1) if listening_stats['avg_band'] else 0.0
    listening_percentage = int((real_listening_score / 9.0) * 100) if real_listening_score > 0 else 0

    real_writing_score = 0.0
    writing_percentage = 0

    real_speaking_score = 0.0
    speaking_percentage = 0

    context = {
        'user': user,
        'is_premium': getattr(user, 'is_premium', False),
        'current_streak': streak_obj.current_streak,
        'latest_score': latest_score,
        'best_score': best_score,
        'bands_to_close': round(bands_to_close, 1) if bands_to_close > 0 else "0.0",
        
        'leaderboard': leaderboard_data, 
        'show_footer_user': show_footer_user,
        'footer_user': current_user_data,
        
        'daily_plan': {
            'title': 'Bugungi dars rejasi',
            'modules': modules_list 
        },
        'skill_matrix': [
            {
                'name': 'Listening', 
                'icon': '🎧', 
                'score': f"{real_listening_score:.1f}" if real_listening_score > 0 else "—", 
                'percentage': listening_percentage if listening_percentage > 0 else 10, # <-- Ставит 10% базовой ширины если нет тестов
                'color': '#2563eb'
            },
            {
                'name': 'Reading', 
                'icon': '📕', 
                'score': f"{real_reading_score:.1f}" if real_reading_score > 0 else "—", 
                'percentage': reading_percentage if reading_percentage > 0 else 10,
                'color': '#10b981'
            },
            {
                'name': 'Writing', 
                'icon': '📝', 
                'score': f"{real_writing_score:.1f}" if real_writing_score > 0 else "—", 
                'percentage': writing_percentage, 
                'color': '#f59e0b'
            },
            {
                'name': 'Speaking', 
                'icon': '🗣️', 
                'score': f"{real_speaking_score:.1f}" if real_speaking_score > 0 else "—", 
                'percentage': speaking_percentage, 
                'color': '#ec4899'
            },
        ]
    }
    
    return render(request, 'dashboard.html', context)

@csrf_exempt 
def plans_view(request):
    user_id = request.session.get("user_id")
    if not user_id:
        if request.method == "POST":
            return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=401)
        return redirect("register")

    try:
        user = IeltsUser.objects.get(id=user_id)
    except IeltsUser.DoesNotExist:
        if request.method == "POST":
            return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)
        return redirect("register")

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            
            ielts_background = data.get("ielts_background")
            want_result = data.get("want_result")
            challenges = data.get("challenges")
            exam_timeline = data.get("exam_timeline")
            daily_study_time = data.get("daily_study_time")

            if isinstance(challenges, list):
                challenges_str = ", ".join(challenges)
            else:
                challenges_str = str(challenges) if challenges else ""

            user.ielts_background = ielts_background
            user.want_result = float(want_result) if want_result else 7.5
            user.challenges = challenges_str
            user.exam_timeline = exam_timeline
            user.daily_study_time = daily_study_time
            user.save()

            return JsonResponse({'status': 'success', 'redirect_url': '/oferta'}, status=200)

        except (ValueError, KeyError, TypeError) as e:
            return JsonResponse({'status': 'error', 'message': f'Data processing error: {str(e)}'}, status=400)

    return render(request, "plans2.html", {"user": user})