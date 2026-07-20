from django.contrib import admin
from . models import IeltsUser, DailyTask,  UserStreak, MockResult

admin.site.register(IeltsUser)
admin.site.register(DailyTask)
admin.site.register(UserStreak)
admin.site.register(MockResult)