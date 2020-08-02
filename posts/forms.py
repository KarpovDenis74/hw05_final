from django import forms
from django.forms import ModelForm
from .models import Post, Comment


class PostForm(ModelForm):
    def clean_text(self):
        if self.cleaned_data['text'] is None:
            raise forms.ValidationError(
                    'Пожалуйста, заполните это поле',
                    params={'value': self.cleaned_data['text']},
            )
        return self.cleaned_data['text']

    class Meta:
        model = Post
        fields = ['text', 'group', 'image']
        labels = {
            'group': 'Сообщество'
        }
        help_texts = {
            'group': 'Выберите сообщество для поста',
            'text': 'Здесь нужно ввести текст поста'
        }


class CommentForm(ModelForm):
    def clean_text(self):
        if self.cleaned_data['text'] is None:
            raise forms.ValidationError(
                'Пожалуйста, заполните это поле',
                params={'value': self.cleaned_data['text']},
            )
        return self.cleaned_data['text']

    class Meta:
        model = Comment
        fields = ['text']
        labels = {
            'text': 'Прокомментируйте этот пост'
        }
        help_texts = {
            'text': 'Здесь нужно ввести текст комментрия'
        }
