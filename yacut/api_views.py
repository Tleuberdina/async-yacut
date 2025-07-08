import re

from flask import jsonify, request

from . import app, db
from .error_handlers import InvalidAPIUsage
from .models import URLMap
from .views import get_unique_short_id


@app.route('/api/id/<short_id>/', methods=['GET'])
def get_urlmap(short_id):
    """
    Обработчик get-запросов к api на получение
    оригинальной ссылки по указанному короткому идентификатору.
    """
    urlmap = URLMap.query.filter_by(short=short_id).first()
    if urlmap is None:
        raise InvalidAPIUsage('Указанный id не найден', 404)
    return jsonify({'url': urlmap.original}), 200


@app.route('/api/id/', methods=['POST'])
def add_urlmap():
    """
    Обработчик post-запросов к api на создание новой короткой ссылки.
    """
    data = request.get_json(force=True, silent=True)
    if data == {} or not data:
        raise InvalidAPIUsage('Отсутствует тело запроса', 400)
    reserved_words = ['files', 'admin', 'api']
    if 'url' not in data:
        raise InvalidAPIUsage('"url" является обязательным полем!', 400)
    if 'custom_id' not in data or not data['custom_id']:
        max_attempts = 10
        for _ in range(max_attempts):
            short_url = get_unique_short_id()
            if (
                short_url not in reserved_words and
                not URLMap.query.filter_by(short=short_url).first()
            ):
                break
    else:
        short_url = data['custom_id']
        if not re.fullmatch(r'^[a-zA-Z0-9]{1,16}$', short_url):
            raise InvalidAPIUsage(
                'Указано недопустимое имя для короткой ссылки', 400
            )
        if (
            URLMap.query.filter_by(short=short_url).first() is not None
            or short_url in reserved_words
        ):
            raise InvalidAPIUsage(
                'Предложенный вариант короткой ссылки уже существует.'
            )
    urlmap = URLMap()
    urlmap.original = data.get('url', urlmap.original)
    urlmap.short = short_url
    urlmap.from_dict(data)
    db.session.add(urlmap)
    db.session.commit()
    full_short_url = f'{request.host_url}{short_url}'
    return jsonify({
        'url': urlmap.original,
        'short_link': full_short_url
    }), 201
