from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

    def clean_text(self):
        """Метод-валидатор для поля 'text'"""
        data = self.cleaned_data['text']
        if not data:
            raise forms.ValidationError('Это поле нужно заполнить!')

        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)

    def clean_text(self):
        """Метод-валидатор при создании комментария."""
        data = self.cleaned_data['text']
        if not data:
            raise forms.ValidationError(
                'Здесь должен быть текст! Без него не получится...'
            )
        return data
