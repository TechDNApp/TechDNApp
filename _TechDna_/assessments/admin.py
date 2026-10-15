from django.contrib import admin

from .models import Answer, Assessment, Attempt, Question, Result


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "owner",
        "technology",
        "role",
        "mode",
        "active",
        "created_at",
    )
    list_filter = ("mode", "active", "technology", "role")
    search_fields = ("title", "description", "owner__username")
    list_select_related = ("owner", "technology", "role")
    inlines = [QuestionInline]


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("__str__", "assessment", "difficulty")
    list_filter = ("difficulty", "assessment")
    inlines = [AnswerInline]


admin.site.register(Attempt)
admin.site.register(Result)
