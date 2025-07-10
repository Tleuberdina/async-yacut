from http import HTTPStatus
import re

from flask import jsonify, request

from . import app
from .constants import ACCEPTABLE_VALUE, MESSAGE_UNACCEPTABLE_NAME
from .error_handlers import InvalidAPIUsage
from .models import URLMap


@app.route('/api/id/<short_id>/', methods=['GET'])
def get_urlmap(short_id):
    """
    Обработчик get-запросов к api на получение
    оригинальной ссылки по указанному короткому идентификатору.
    """
    urlmap = URLMap.get_urlmap(short_id)
    if urlmap is None:
        raise InvalidAPIUsage(
            'Указанный id не найден',
            HTTPStatus.NOT_FOUND
        )
    return jsonify({'url': urlmap.original}), HTTPStatus.OK


@app.route('/api/id/', methods=['POST'])
def add_urlmap_api_view():
    """
    Обработчик post-запросов к api на создание новой короткой ссылки.
    """
    data = request.get_json(force=True, silent=True)
    if not data:
        raise InvalidAPIUsage(
            'Отсутствует тело запроса',
            HTTPStatus.BAD_REQUEST
        )
    if 'url' not in data:
        raise InvalidAPIUsage(
            '"url" является обязательным полем!',
            HTTPStatus.BAD_REQUEST
        )
    custom_id = data.get('custom_id')
    if custom_id:
        if not re.fullmatch(ACCEPTABLE_VALUE, custom_id):
            raise InvalidAPIUsage(
                MESSAGE_UNACCEPTABLE_NAME,
                HTTPStatus.BAD_REQUEST
            )
    urlmap = URLMap.create(
        original_link=data['url'],
        custom_id=custom_id
    )
    return jsonify(urlmap.to_dict()), HTTPStatus.CREATED
