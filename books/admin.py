from django.contrib import admin
from .models import Books,Category,Authors,Languages,Identifier,Tag,Review
# Register your models here.
admin.site.register(Books)
admin.site.register(Category)
admin.site.register(Authors)
admin.site.register(Languages)
admin.site.register(Identifier)
admin.site.register(Tag)
admin.site.register(Review)