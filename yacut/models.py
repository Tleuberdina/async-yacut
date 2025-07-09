from datetime import datetime
from http import HTTPStatus
import random
import re
import string

from flask import url_for

from . import db
from .constants import (ACCEPTABLE_VALUE, LENGTH_CODE, MAX_ATTEMPTS,
                        MAX_LENGTH, RESERVED_WODS)
from .error_handlers import InvalidAPIUsage


class URLMap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original = db.Column(db.String(), nullable=False)
    short = db.Column(db.String(MAX_LENGTH), unique=True, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def to_dict(self, api_format=False):
        if api_format:
            return {
                'url': self.original,
                'short_link': url_for(
                    'urlmap_view',
                    short=self.short,
                    _external=True
                )
            }
        return {
            'short_url': url_for(
                'urlmap_view',
                short=self.short,
                _external=True
            ),
            'original_url': self.original
        }

    def from_dict(self, data):
        for field in ['original', 'short']:
            if field in data:
                setattr(self, field, data[field])

    @classmethod
    def generate_short_id(cls, length=LENGTH_CODE):
        chars = string.ascii_letters + string.digits
        return ''.join(random.choices(chars, k=length))

    @staticmethod
    def create(original_link, custom_id=None):
        if not custom_id:
            for _ in range(MAX_ATTEMPTS):
                short_url = URLMap.generate_short_id()
                if (
                    short_url not in RESERVED_WODS and
                    not URLMap.query.filter_by(short=short_url).first()
                ):
                    break
        else:
            short_url = custom_id
            if not re.fullmatch(ACCEPTABLE_VALUE, short_url):
                raise InvalidAPIUsage(
                    'Указано недопустимое имя для короткой ссылки',
                    HTTPStatus.BAD_REQUEST
                )
            if (
                URLMap.query.filter_by(short=short_url).first() is not None
                or short_url in RESERVED_WODS
            ):
                raise InvalidAPIUsage(
                    'Предложенный вариант короткой ссылки уже существует.'
                )
        urlmap = URLMap(
            original=original_link,
            short=short_url
        )
        db.session.add(urlmap)
        db.session.commit()
        return urlmap

    @staticmethod
    def get_urlmap_or_404(short_id):
        urlmap = URLMap.query.filter_by(short=short_id).first()
        if urlmap is None:
            raise InvalidAPIUsage(
                'Указанный id не найден',
                HTTPStatus.NOT_FOUND
            )
        return urlmap