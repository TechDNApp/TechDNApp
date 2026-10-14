from django.contrib import admin
from .models import Category

from .models import (
    Category,
    Technology,
    Role,
    Skill,
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "created_at",
    )

    search_fields = (
        "name",
    )
    
admin.site.register(Technology)
admin.site.register(Role)
admin.site.register(Skill)