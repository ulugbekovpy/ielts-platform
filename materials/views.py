import json
import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from .models import ReadingTest, ReadingResult
from main.models import IeltsUser, UserStreak  # Импортируем нужные модели из main

def reading_test_view(request, test_id):
    test = get_object_or_404(ReadingTest, id=test_id)
    user_id = request.session.get("user_id")
    if not user_id:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.method == 'POST':
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        return redirect('login')

    try:
        user = IeltsUser.objects.get(id=user_id)
    except IeltsUser.DoesNotExist:
        return redirect('login')
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            score = int(data.get('score'))
            band = float(data.get('band'))
            time_spent = data.get('time_spent', '00:00')
            
            ReadingResult.objects.create(
                user=user, 
                test=test,
                score=score,
                band=band,
                time_spent=time_spent
            )
            return JsonResponse({'status': 'success', 'message': 'Result saved successfully!'})
            
        except (ValueError, TypeError, KeyError):
            return JsonResponse({'status': 'error', 'message': 'Invalid data format'}, status=400)

    return render(request, test.template_name)


from django.shortcuts import render, redirect
from django.utils import timezone
from .models import ReadingTest, ReadingResult  # Убедись, что импорты моделей правильные
from main.models import IeltsUser  # Или откуда импортируется твоя модель пользователя
from datetime import timedelta

def daily_reading_view(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    try:
        user = IeltsUser.objects.get(id=user_id)
    except IeltsUser.DoesNotExist:
        return redirect("login")

    is_premium = getattr(user, 'is_premium', False)
    today = timezone.now().date()
    now = timezone.now()

    # Получаем все тесты по порядку
    all_tests = ReadingTest.objects.all().order_by('id')
    
    # Определяем, какой тест сегодня является "дневным" (daily)
    day_of_year = now.timetuple().tm_yday
    total_tests = all_tests.count()
    
    daily_test_index = day_of_year % total_tests if total_tests > 0 else 0

    tests_data = []
    for index, test in enumerate(all_tests):
        # 1. Проверяем, разблокирован ли тест
        # На бесплатном тарифе доступен только сегодняшний ежедневный тест. На премиуме — все.
        is_today = (index == daily_test_index)
        is_unlocked = is_premium or is_today

        # 2. Ищем последний результат пользователя по этому тесту
        latest_result = ReadingResult.objects.filter(user=user, test=test).order_by('-submitted_at').first()
        
        is_completed = latest_result is not None
        score_band = f"{latest_result.band:.1f}" if is_completed and latest_result.band else None

        # 3. Рассчитываем кулдаун в 1 час (3600 секунд) для бесплатного тарифа
        cooldown_seconds = 0
        if is_completed and latest_result and not is_premium:
            elapsed_time = now - latest_result.submitted_at
            remaining_time = timedelta(hours=1) - elapsed_time
            if remaining_time.total_seconds() > 0:
                cooldown_seconds = int(remaining_time.total_seconds())

        # Собираем объект для передачи в шаблон
        tests_data.append({
            'test': test,
            'number': index + 1,
            'is_today': is_today,
            'is_unlocked': is_unlocked,
            'is_completed': is_completed,
            'score_band': score_band,
            'cooldown_seconds': cooldown_seconds,
        })

    # Рассчитываем время до полуночи для верхнего таймера ("Keyingi testga")
    tomorrow = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    seconds_left = int((tomorrow - now).total_seconds())

    context = {
        'user': user,
        'is_premium': is_premium,
        'current_streak': getattr(user.userstreak, 'current_streak', 0) if hasattr(user, 'userstreak') else 0,
        'tests': tests_data,
        'seconds_left': seconds_left,
    }
    
    return render(request, 'reading.html', context)


import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .models import ListeningTest, ListeningResult
from main.models import IeltsUser

# 1. Прохождение теста по Listening (GET/POST)
def listening_test_view(request, test_id):
    test = get_object_or_404(ListeningTest, id=test_id)
    user_id = request.session.get("user_id")
    if not user_id:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.method == 'POST':
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        return redirect('login')

    try:
        user = IeltsUser.objects.get(id=user_id)
    except IeltsUser.DoesNotExist:
        return redirect('login')
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            score = int(data.get('score'))
            band = float(data.get('band'))
            time_spent = data.get('time_spent', '00:00')
            
            ListeningResult.objects.create(
                user=user, 
                test=test,
                score=score,
                band=band,
                time_spent=time_spent
            )
            return JsonResponse({'status': 'success', 'message': 'Listening result saved successfully!'})
            
        except (ValueError, TypeError, KeyError):
            return JsonResponse({'status': 'error', 'message': 'Invalid data format'}, status=400)

    return render(request, test.template_name)


# 2. Общий список Listening тестов (Daily & Unlocked)
def daily_listening_view(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    try:
        user = IeltsUser.objects.get(id=user_id)
    except IeltsUser.DoesNotExist:
        return redirect("login")

    is_premium = getattr(user, 'is_premium', False)
    today = timezone.now().date()
    now = timezone.now()

    # Все аудирования по порядку
    all_tests = ListeningTest.objects.all().order_by('id')
    
    # "Challenge дня" на основе текущих суток
    day_of_year = now.timetuple().tm_yday
    total_tests = all_tests.count()
    daily_test_index = day_of_year % total_tests if total_tests > 0 else 0

    tests_data = []
    for index, test in enumerate(all_tests):
        is_today = (index == daily_test_index)
        is_unlocked = is_premium or is_today

        # Ищем последнюю сдачу аудио-теста
        latest_result = ListeningResult.objects.filter(user=user, test=test).order_by('-submitted_at').first()
        is_completed = latest_result is not None
        score_band = f"{latest_result.band:.1f}" if is_completed and latest_result.band else None

        # Ограничение повторной сдачи: 1 час для базового тарифа
        cooldown_seconds = 0
        if is_completed and latest_result and not is_premium:
            elapsed_time = now - latest_result.submitted_at
            remaining_time = timedelta(hours=1) - elapsed_time
            if remaining_time.total_seconds() > 0:
                cooldown_seconds = int(remaining_time.total_seconds())

        tests_data.append({
            'test': test,
            'number': index + 1,
            'is_today': is_today,
            'is_unlocked': is_unlocked,
            'is_completed': is_completed,
            'score_band': score_band,
            'cooldown_seconds': cooldown_seconds,
        })

    # Время до следующего дня для глобального таймера
    tomorrow = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    seconds_left = int((tomorrow - now).total_seconds())

    context = {
        'user': user,
        'is_premium': is_premium,
        'current_streak': getattr(user.userstreak, 'current_streak', 0) if hasattr(user, 'userstreak') else 0,
        'tests': tests_data,
        'seconds_left': seconds_left,
    }
    
    return render(request, 'listening.html', context)






# import json
# import google.generativeai as genai
# from django.shortcuts import render, get_object_or_404, redirect
# from django.http import JsonResponse
# from django.utils import timezone
# from .models import WritingTest, WritingResult
# from main.models import IeltsUser

# # Конфигурируем Gemini API ключ (добавь свой ключ)
# genai.configure(api_key="AIzaSyAzXejxUiT_DQsE49iwNusqYvN2KGxOgBA")

# def writing_test_view(request, test_id):
#     test = get_object_or_404(WritingTest, id=test_id)
#     user_id = request.session.get("user_id")
#     if not user_id:
#         return redirect('login')

#     user = get_object_or_404(IeltsUser, id=user_id)

#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             user_text = data.get('user_answer', '').strip()
#             time_spent = data.get('time_spent', '00:00')
#             word_count = len(user_text.split())

#             if not user_text:
#                 return JsonResponse({'status': 'error', 'message': 'Matn bo\'sh bo\'lishi mumkin emas'}, status=400)

#             # Формируем системный промпт для Gemini, чтобы получить строго JSON на выходе
#             system_prompt = f"""
#             You are an official IELTS Writing Examiner. Evaluate the following student's response for IELTS {test.get_task_type_display()}.
            
#             Question Prompt:
#             {test.question_text}
            
#             Student's Response:
#             {user_text}
            
#             Evaluate strictly based on the 4 IELTS criteria:
#             1. Task Achievement / Task Response (TA)
#             2. Coherence and Cohesion (CC)
#             3. Lexical Resource (LR)
#             4. Grammatical Range and Accuracy (GRA)
            
#             You must return the response ONLY as a clean, valid JSON object (no markdown blocks, no '```json'). Use this exact template:
#             {{
#                 "band": 6.5,
#                 "ta": 6.0,
#                 "cc": 7.0,
#                 "lr": 6.5,
#                 "gra": 6.5,
#                 "feedback": "Detailed overall critique in Uzbek language (O'zbek tilida). Point out specific strengths and main areas of improvement.",
#                 "corrections": [
#                     {{"original": "wrong phrase", "corrected": "right phrase", "explanation": "O'zbek tilida tushuntirish"}}
#                 ]
#             }}
#             Calculate the overall band score as the mathematical average of the four criteria, rounded to the nearest half band.
#             """

#             # Вызываем модель Gemini
#             model = genai.GenerativeModel("gemini-1.5-flash")
#             response = model.generate_content(system_prompt)
            
#             # Парсим JSON ответ от AI
#             clean_json_str = response.text.replace("```json", "").replace("```", "").strip()
#             ai_data = json.loads(clean_json_str)

#             # Сохраняем результат в базу данных
#             result_obj = WritingResult.objects.create(
#                 user=user,
#                 test=test,
#                 user_answer=user_text,
#                 band=float(ai_data.get('band', 4.0)),
#                 task_achievement=float(ai_data.get('ta', 4.0)),
#                 coherence_cohesion=float(ai_data.get('cc', 4.0)),
#                 lexical_resource=float(ai_data.get('lr', 4.0)),
#                 grammar_accuracy=float(ai_data.get('gra', 4.0)),
#                 ai_feedback=clean_json_str, # Сохраняем весь JSON-пакет для фронтенда
#                 word_count=word_count,
#                 time_spent=time_spent
#             )

#             return JsonResponse({
#                 'status': 'success', 
#                 'message': 'Essey muvaffaqiyatli tekshirildi!',
#                 'evaluation': ai_data
#             })

#         except Exception as e:
#             return JsonResponse({'status': 'error', 'message': f'AI evaluation failed: {str(e)}'}, status=500)

#     return render(request, 'writing_test.html', {'test': test, 'user': user})

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import VocabularyCategory, VocabularyWord
from main.models import IeltsUser
from datetime import timedelta

def daily_vocabulary_view(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    try:
        user = IeltsUser.objects.get(id=user_id)
    except IeltsUser.DoesNotExist:
        return redirect("login")

    is_premium = getattr(user, 'is_premium', False)
    now = timezone.now()

    # Получаем все доступные категории слов
    all_categories = VocabularyCategory.objects.all().order_by('id')
    total_categories = all_categories.count()

    # Рассчитываем сегодняшнюю тему по дню года
    day_of_year = now.timetuple().tm_yday
    daily_category_index = day_of_year % total_categories if total_categories > 0 else 0

    categories_data = []
    for index, category in enumerate(all_categories):
        is_today = (index == daily_category_index)
        is_unlocked = is_premium or is_today

        # Извлекаем слова для этой категории
        # На бесплатном тарифе ограничиваем тему 10 словами для компактного ежедневного изучения
        words_query = category.words.all()
        if not is_premium:
            words_query = words_query[:10]

        words_list = []
        for w in words_query:
            words_list.append({
                'word': w.word,
                'translation': w.translation,
                'example': w.example,
                'band': w.band
            })

        categories_data.append({
            'id': category.id,
            'title': category.title,
            'icon': category.icon,
            'is_today': is_today,
            'is_unlocked': is_unlocked,
            'words': words_list,
            'words_count': len(words_list)
        })

    # Время до следующего дня
    tomorrow = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    seconds_left = int((tomorrow - now).total_seconds())

    context = {
        'user': user,
        'is_premium': is_premium,
        'current_streak': getattr(user.userstreak, 'current_streak', 0) if hasattr(user, 'userstreak') else 0,
        'categories': categories_data,
        'seconds_left': seconds_left,
    }
    
    return render(request, 'vocabulary.html', context)