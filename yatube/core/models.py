from django.db import models


class CreatedModel(models.Model):
    '''Абстрактная модель. Добавляет дату публикации.'''
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )

    class Meta:
        abstract = True
