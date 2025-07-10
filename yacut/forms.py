from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, MultipleFileField
from wtforms import SubmitField, URLField
from wtforms.validators import DataRequired, Length, Optional, Regexp

from .constants import (ACCEPTABLE_VALUE, MESSAGE_UNACCEPTABLE_NAME,
                        FILE_EXTENSION, MAX_LENGTH, MIN_LENGTH)


class URLMapMainForm(FlaskForm):
    original_link = URLField(
        'Длинная ссылка',
        validators=[DataRequired(message='Обязательное поле')]
    )
    custom_id = URLField(
        'Ваш вариант короткой ссылки',
        validators=[
            Length(
                MIN_LENGTH,
                MAX_LENGTH,
                message=f'Длина должна быть от {MIN_LENGTH}'
                        f'до {MAX_LENGTH} символов'
            ),
            Regexp(
                ACCEPTABLE_VALUE,
                message=MESSAGE_UNACCEPTABLE_NAME
            ),
            Optional()
        ]
    )
    submit = SubmitField('Создать')


class URLMapForm(FlaskForm):
    files = MultipleFileField(
        validators=[
            FileAllowed(
                FILE_EXTENSION,
                message=(
                    'Выберите файлы с расширением '
                    + ', '.join(f'.{ext}' for ext in sorted(FILE_EXTENSION))
                )
            )
        ]
    )
    submit = SubmitField('Загрузить')
