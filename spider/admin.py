from django.contrib import admin

from spider.models import SpiderProfile, SpiderSession, URLResult


class SpiderProfileAdmin(admin.ModelAdmin):
    list_display = ('title', 'url',)


class SpiderSessionAdmin(admin.ModelAdmin):
    list_display = ('spider_profile', 'created_date',)
    list_filter = ('spider_profile',)


class URLResultAdmin(admin.ModelAdmin):
    list_display = ('url', 'response_status', 'response_time', 'created_date',)
    list_filter = ('response_status',)


admin.site.register(SpiderProfile, SpiderProfileAdmin)
admin.site.register(SpiderSession, SpiderSessionAdmin)
admin.site.register(URLResult, URLResultAdmin)
