from django.db import models
from main.models import IeltsUser

class ReadingTest(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название теста")
    template_name = models.CharField(
        max_length=255, 
        verbose_name="Путь к HTML файлу", 
        help_text="Например: tests/olive_oil.html"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class ReadingResult(models.Model):
    user = models.ForeignKey(IeltsUser, on_delete=models.CASCADE)
    test = models.ForeignKey(ReadingTest, on_delete=models.CASCADE)
    score = models.IntegerField() 
    band = models.FloatField() 
    time_spent = models.CharField(max_length=10) 
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Result #{self.id} of student {self.user}"
    

class ListeningTest(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название теста")
    template_name = models.CharField(
        max_length=255, 
        verbose_name="Путь к HTML файлу", 
        help_text="Например: tests/listening_oil.html"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class ListeningResult(models.Model):
    user = models.ForeignKey(IeltsUser, on_delete=models.CASCADE)
    test = models.ForeignKey(ListeningTest, on_delete=models.CASCADE)
    score = models.IntegerField() 
    band = models.FloatField() 
    time_spent = models.CharField(max_length=10) 
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Listening Result #{self.id} of student {self.user}"
    

class VocabularyCategory(models.Model):
    title = models.CharField(max_length=255, verbose_name="Mavzu sarlavhasi")
    icon = models.CharField(
        max_length=50, 
        default="fa-seedling", 
        help_text="FontAwesome klass nomi, masalan: fa-seedling, fa-graduation-cap"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __img__(self):
        return self.title

class VocabularyWord(models.Model):
    category = models.ForeignKey(VocabularyCategory, on_delete=models.CASCADE, related_name="words")
    word = models.CharField(max_length=100, verbose_name="Inglizcha so'z")
    translation = models.TextField(verbose_name="Tushuntirish yoki tarjimasi (O'zbek tilida)")
    example = models.TextField(verbose_name="Gapda ishlatilishi (Example)")
    band = models.CharField(max_length=10, default="Band 7.0+", verbose_name="IELTS Band darajasi")

    def __str__(self):
        return f"{self.word} ({self.category.title})"