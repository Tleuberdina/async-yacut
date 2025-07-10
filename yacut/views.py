from flask import Response, redirect, request, render_template
import requests

from . import app, db
from .disk import async_upload_files_to_disk
from .forms import URLMapForm, URLMapMainForm
from .models import URLMap


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
    if not form.validate_on_submit():
        return render_template('urlmap.html', form=form, short_url=None)
    short_url = None
    urlmap = URLMap.create(
        original_link=form.original_link.data,
        custom_id=form.custom_id.data,
        validate=False,
        form=form
    )
    if isinstance(urlmap, dict):
        return render_template(
            urlmap['error_template'],
            form=urlmap['form']
        )
    short_url = urlmap.to_dict()['short_link']
    return render_template(
        'urlmap.html',
        form=form,
        short_url=short_url
    )


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
            short_url = URLMap.generate_short_id()
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
    return render_template('urlmap_files.html', form=form)
