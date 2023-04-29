from django.db import models


class CreatedModel(models.Model):
    '''Абстрактная модель. Добавляет дату публикации.'''
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        help_text='Отображает дату'
    )

    class Meta:
        abstract = True
