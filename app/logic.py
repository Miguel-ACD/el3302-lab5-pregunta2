"""Lógica de negocio y generación de campaña."""
import os
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
import imageio_ffmpeg


def scripts(brand, product, audience):
    return [
        {"title":"Presentación directa", "text":f"¿Buscas {product}? {brand} tiene una opción pensada para {audience}. Descúbrela hoy.", "cta":"Conoce más"},
        {"title":"Problema y solución", "text":f"Para {audience}, encontrar {product} puede ser complicado. {brand} te ayuda a dar el siguiente paso.", "cta":"Escríbenos"},
        {"title":"Invitación cercana", "text":f"Haz espacio para algo nuevo. {product} de {brand}: una propuesta para {audience}.", "cta":"Descúbrelo"},
    ]


def validate_image(stream):
    image=Image.open(stream)
    image.verify()
    stream.seek(0)
    image=Image.open(stream)
    if image.format not in ('JPEG','PNG','WEBP'):
        raise ValueError('Usa una imagen JPG, PNG o WEBP.')
    return ImageOps.exif_transpose(image).convert('RGB')


def make_media(campaign):
    base=Path(os.environ.get('DATA_DIR','/data'))/str(campaign['id'])
    base.mkdir(parents=True,exist_ok=True)
    photo=Image.open(base/'original.jpg').convert('RGB')
    script=campaign['scripts'][campaign['selected']]
    fonts=Path(__file__).parent/'fonts'
    body_font=ImageFont.truetype(str(fonts/'IBMPlexSans-Regular.ttf'),26)
    label_font=ImageFont.truetype(str(fonts/'IBMPlexSans-Bold.ttf'),28)
    title_font=ImageFont.truetype(str(fonts/'IBMPlexSans-Bold.ttf'),46)
    palettes=[('#142b30','#f0e8d8'),('#2c2537','#eee6f3'),('#30281e','#f5e9d3')]
    for i,(bg,fg) in enumerate(palettes,1):
        canvas=Image.new('RGB',(720,1280),bg)
        crop=ImageOps.fit(photo,(720,720),method=Image.Resampling.LANCZOS,centering=(0.5,0.5))
        canvas.paste(crop,(0,0))
        draw=ImageDraw.Draw(canvas)
        draw.rectangle((0,720,720,1280),fill=bg)
        draw.text((42,765),campaign['brand'][:30],font=label_font,fill=fg)
        heading=[campaign['product'],script['title'],script['cta']][i-1]
        draw.text((42,840),heading[:25],font=title_font,fill=fg)
        words=script['text'].split()
        lines=[]; line=''
        for word in words:
            test=(line+' '+word).strip()
            if len(test)>37:
                lines.append(line); line=word
            else: line=test
        lines.append(line)
        for j,text in enumerate(lines[:4]):
            draw.text((42,940+j*48),text,font=body_font,fill=fg)
        canvas.save(base/f'pieza-{i}.jpg',quality=88)
    cmd=[imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-loglevel','error','-y']
    for i in (1,2,3): cmd += ['-loop','1','-t','3','-i',str(base/f'pieza-{i}.jpg')]
    cmd += ['-f','lavfi','-t','9','-i','anullsrc=channel_layout=stereo:sample_rate=48000',
        '-filter_complex','[0:v][1:v][2:v]concat=n=3:v=1:a=0,format=yuv420p[v]',
        '-map','[v]','-map','3:a','-c:v','libx264','-preset','ultrafast','-crf','28',
        '-r','24','-c:a','aac','-b:a','96k','-shortest','-movflags','+faststart',str(base/'video.mp4')]
    subprocess.run(cmd,check=True,timeout=180)
