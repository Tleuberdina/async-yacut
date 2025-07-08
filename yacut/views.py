import random
import re
import string

from flask import Response, flash, redirect, request, render_template
import requests

from . import app, db
from .disk import async_upload_files_to_disk
from .forms import URLMapForm, URLMapMainForm
from .models import URLMap


def get_unique_short_id(length=6):
    """Генерирует код для короткой ссылки."""
    unique_short = string.ascii_letters + string.digits
    short_url = ''.join(random.choice(unique_short) for _ in range(length))
    return short_url


def is_yandex_disk_link(url):
    """Проверяет, является ли ссылка файлом на Яндекс.Диске"""
    return 'yandex.ru/disk' in url or 'yadi.sk' in url or 'yandex.net' in url


@app.route('/<short>')
def urlmap_view(short):
    """
    При переходе по короткой ссылке (short) отображает
    изначальную страницу пользователя(original).
    """
    urlmap = URLMap.query.filter_by(short=short).first_or_404()
    if is_yandex_disk_link(urlmap.original):
        headers = {'Authorization': f'OAuth {app.config["DISK_TOKEN"]}'}
        response = requests.get(urlmap.original, headers=headers, stream=True)
        response.raise_for_status()
        filename = 'file'
        if 'filename=' in urlmap.original.lower():
            filename = urlmap.original.split('filename=')[1].split('&')[0]
        flask_response = Response(
            response.iter_content(chunk_size=8192),
            content_type=response.headers['Content-Type']
        )
        flask_response.headers[
            'Content-Disposition'] = f'attachment; filename="{filename}"'
        return flask_response
    else:
        return redirect(urlmap.original)


@app.route('/', methods=['GET', 'POST'])
def add_urlmap_view():
    """Обрабатывает post-запросы по преобразованию
    длинных ссылок в короткие.
    """
    form = URLMapMainForm()
    short_url = None
    reserved_words = ['files', 'admin', 'api']
    if form.validate_on_submit():
        original_url = form.original_link.data
        custom_id = form.custom_id.data
        if custom_id:
            short_url = custom_id
            if not re.fullmatch(r'^[a-zA-Z0-9]{1,16}$', short_url):
                flash(
                    'Короткая ссылка может содержать латинские буквы и цифры.'
                )
                return render_template('urlmap.html', form=form)
            if (
                short_url in reserved_words
                or URLMap.query.filter_by(short=short_url).first() is not None
            ):
                flash(
                    'Предложенный вариант короткой ссылки уже существует.'
                )
                return render_template('urlmap.html', form=form)
        else:
            max_attempts = 10
            for _ in range(max_attempts):
                short_url = get_unique_short_id()
                if (
                    short_url not in reserved_words and
                    not URLMap.query.filter_by(short=short_url).first()
                ):
                    break
        urlmap = URLMap(
            original=original_url,
            short=short_url
        )
        db.session.add(urlmap)
        db.session.commit()
        full_short_url = f'{request.host_url}{short_url}'
        return render_template(
            'urlmap.html',
            form=form,
            short_url=full_short_url
        )
    return render_template('urlmap.html', form=form, short_url=None)


@app.route('/files', methods=['GET', 'POST'])
async def add_urlmap_files_view():
    """Асинхронная функция обработки post-запросов
    загрузки файлов и генерации коротких ссылок к ним.
    """
    form = URLMapForm()
    if form.validate_on_submit():
        download_info = await async_upload_files_to_disk(form.files.data)
        file_names = [info['name'] for info in download_info]
        download_links = [info['url'] for info in download_info]
        files_data = []
        for name, link in zip(file_names, download_links):
            max_attempts = 10
            for _ in range(max_attempts):
                short_url = get_unique_short_id()
                if not URLMap.query.filter_by(short=short_url).first():
                    break
            urlmap = URLMap(
                original=link,
                short=short_url
            )
            db.session.add(urlmap)
            files_data.append({
                'name': name,
                'short_url': f'{request.host_url}{short_url}'
            })
        db.session.commit()
        original = file_names[0] if len(file_names) == 1 else file_names
        return render_template(
            'urlmap_files.html',
            form=form,
            original=original,
            files_data=files_data
        )
    return render_template('urlmap_files.html', form=form, short_url=None)
