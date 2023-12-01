from django.contrib import admin
from .models import User, Project, Conversation, Text

admin.site.register(User)
admin.site.register(Project)
admin.site.register(Conversation)
admin.site.register(Text)

