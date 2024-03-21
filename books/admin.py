from django.contrib import admin
from .models import Books,Category,Authors,Languages,Identifier,Tag,Review,Like,UserLibrary,SocialMediaLink,Notification,NotificationType,Report,Folder,UserBook,Chapter
# Register your models here.
admin.site.register(Books)
admin.site.register(Category)
admin.site.register(Authors)
admin.site.register(Languages)
admin.site.register(Identifier)
admin.site.register(Tag)
admin.site.register(Review)
admin.site.register(Like)
admin.site.register(UserLibrary)
admin.site.register(SocialMediaLink)
admin.site.register(Notification)
admin.site.register(Report)
admin.site.register(Folder)
admin.site.register(UserBook)
admin.site.register(Chapter)



