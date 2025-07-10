from datetime import datetime
import random
import string

from flask import url_for

from . import db
from .constants import (LENGTH_CODE, MAX_ATTEMPTS, MAX_LENGTH,
                        MESSAGE_NAME_ALREADY_EXISTS, RESERVED_WORDS)
from .error_handlers import InvalidAPIUsage


class URLMap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original = db.Column(db.String(), nullable=False)
    short = db.Column(db.String(MAX_LENGTH), unique=True, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def to_dict(self):
        """Преобразует объект модели в словарь."""
        return {
            'short_link': url_for(
                'urlmap_view',
                short=self.short,
                _external=True
            ),
            'url': self.original
        }

    def from_dict(self, data):
        """"
        Добавлять в пустой объект класса значения полей,
        которые получены в post-запросе.
        """
        for field in ['original', 'short']:
            if field in data:
                setattr(self, field, data[field])

    @staticmethod
    def get_urlmap(short_id):
        """Возвращает объект из БД."""
        return URLMap.query.filter_by(short=short_id).first()

    @classmethod
    def generate_short_id(cls, length=LENGTH_CODE):
        """Генерирует уникальный код."""
        for _ in range(MAX_ATTEMPTS):
            chars = string.ascii_letters + string.digits
            short_id = ''.join(random.choices(chars, k=length))
            if (
                short_id not in RESERVED_WORDS and
                not cls.get_urlmap(short_id)
            ):
                break
        return short_id

    @staticmethod
    def create(original_link, custom_id=None):
        """Универсальный метод для создания объекта."""
        if custom_id:
            if (
                URLMap.get_urlmap(custom_id) is not None
                or custom_id in RESERVED_WORDS
            ):
                raise InvalidAPIUsage(MESSAGE_NAME_ALREADY_EXISTS)
            short_url = custom_id
        else:
            short_url = URLMap.generate_short_id()
        urlmap = URLMap(
            original=original_link,
            short=short_url
        )
        db.session.add(urlmap)
        db.session.commit()
        return urlmap
