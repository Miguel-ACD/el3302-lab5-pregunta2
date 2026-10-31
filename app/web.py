"""Presentación web. Ninguna ruta espera a la generación de video."""
import os
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, abort
from . import data, logic


def create_app():
    app=Flask(__name__)
    app.secret_key=os.environ.get('FLASK_SECRET_KEY','solo-desarrollo-local')
    app.config['MAX_CONTENT_LENGTH']=8*1024*1024
    data.init()

    @app.get('/')
    def index():
        return render_template('index.html',campaigns=data.latest())

    @app.post('/campaigns')
    def create():
        brand=request.form.get('brand','').strip()[:60]
        product=request.form.get('product','').strip()[:80]
        audience=request.form.get('audience','').strip()[:80]
        if not all((brand,product,audience)) or 'photo' not in request.files:
            flash('Completa los campos y selecciona una foto.'); return redirect(url_for('index'))
        try:
            image=logic.validate_image(request.files['photo'].stream)
        except Exception:
            flash('La foto debe ser JPG, PNG o WEBP y pesar menos de 8 MB.'); return redirect(url_for('index'))
        scripts=logic.scripts(brand,product,audience)
        id=data.create(brand,product,audience,'original.jpg',scripts)
        folder=Path(os.environ.get('DATA_DIR','/data'))/str(id)
        folder.mkdir(parents=True,exist_ok=True)
        image.save(folder/'original.jpg',quality=88)
        return redirect(url_for('detail',id=id))

    @app.get('/campaigns/<int:id>')
    def detail(id):
        item=data.get(id)
        if not item: abort(404)
        return render_template('detail.html',item=item,publish_ready=bool(os.environ.get('IG_USER_ID') and os.environ.get('IG_ACCESS_TOKEN') and os.environ.get('PUBLISH_PIN')))

    @app.post('/campaigns/<int:id>/select')
    def select(id):
        item=data.get(id)
        if not item: abort(404)
        try: selected=int(request.form.get('selected','-1'))
        except ValueError: selected=-1
        if selected not in (0,1,2):
            flash('Elige uno de los tres guiones.'); return redirect(url_for('detail',id=id))
        data.queue(id,selected)
        return redirect(url_for('detail',id=id))

    @app.get('/campaigns/<int:id>/status')
    def status(id):
        item=data.get(id)
        if not item: abort(404)
        return jsonify(status=item['status'],error=item['error'])

    @app.get('/media/<int:id>/<name>')
    def media(id,name):
        if name not in ('original.jpg','pieza-1.jpg','pieza-2.jpg','pieza-3.jpg','video.mp4'): abort(404)
        if not data.get(id): abort(404)
        return send_from_directory(Path(os.environ.get('DATA_DIR','/data'))/str(id),name)

    @app.post('/campaigns/<int:id>/publish')
    def publish(id):
        item=data.get(id)
        if not item: abort(404)
        pin=os.environ.get('PUBLISH_PIN')
        if not pin or request.form.get('pin')!=pin:
            flash('PIN de publicación incorrecto o no configurado.'); return redirect(url_for('detail',id=id))
        if item['status'] not in ('ready','publish_error'):
            flash('Primero espera a que termine el video.'); return redirect(url_for('detail',id=id))
        data.queue_publish(id)
        return redirect(url_for('detail',id=id))

    @app.get('/health')
    def health(): return {'status':'ok'}

    @app.errorhandler(413)
    def too_large(_):
        flash('La foto supera 8 MB. Elige una más pequeña.'); return redirect(url_for('index'))

    return app
