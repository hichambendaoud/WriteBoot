from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    
    def get_initials(self):
        # Get the user's initials based on their first and last name
        initials = ""
        if self.first_name:
            initials += self.first_name[0]
        if self.last_name:
            initials += self.last_name[0]
        else:
            # If either first name or last name is missing, return the username initial
            initials = self.username[0]
        return initials

    def __str__(self):
        return self.username


class Project(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    active = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Conversation(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    sequence_number = models.PositiveIntegerField(default=1)  # Custom sequence field
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            # Only set sequence number if it's a new conversation
            last_conversation = Conversation.objects.filter(project=self.project).order_by('-sequence_number').first()
            if last_conversation:
                self.sequence_number = last_conversation.sequence_number + 1
            else:
                self.sequence_number = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Conversation {self.sequence_number}"
# - Project: {self.project.name}
class Text(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    text_content = models.TextField()

    def __str__(self):
        return f"Text {self.id} - Conversation: {self.conversation.sequence_number}"