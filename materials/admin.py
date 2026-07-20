from django.contrib import admin
from .models import ReadingTest, ReadingResult, ListeningTest, ListeningResult, VocabularyWord, VocabularyCategory

admin.site.register(ReadingTest)
admin.site.register(ReadingResult)
admin.site.register(ListeningTest)
admin.site.register(ListeningResult)
admin.site.register(VocabularyWord)
admin.site.register(VocabularyCategory)