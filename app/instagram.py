"""Publicación opcional de Reel mediante la API oficial de Meta."""
import os
import time
import requests
from . import data


def publish(campaign):
    user=os.environ.get('IG_USER_ID')
    token=os.environ.get('IG_ACCESS_TOKEN')
    public=os.environ.get('PUBLIC_BASE_URL','').rstrip('/')
    if not user or not token or not public.startswith('https://'):
        raise ValueError('Configura IG_USER_ID, IG_ACCESS_TOKEN y PUBLIC_BASE_URL con HTTPS.')
    root='https://graph.facebook.com/v25.0'
    video=f"{public}/media/{campaign['id']}/video.mp4"
    caption=campaign['scripts'][campaign['selected']]['text']
    response=requests.post(f'{root}/{user}/media',data={
        'media_type':'REELS','video_url':video,'caption':caption,
        'share_to_feed':'false','access_token':token},timeout=30)
    response.raise_for_status()
    container=response.json()['id']
    for _ in range(24):
        time.sleep(5)
        check=requests.get(f'{root}/{container}',params={'fields':'status_code','access_token':token},timeout=15)
        check.raise_for_status()
        status=check.json().get('status_code')
        if status=='FINISHED': break
        if status=='ERROR': raise ValueError('Instagram no pudo procesar el video.')
    else: raise TimeoutError('Instagram sigue procesando el video. Intenta publicar de nuevo.')
    result=requests.post(f'{root}/{user}/media_publish',data={'creation_id':container,'access_token':token},timeout=30)
    result.raise_for_status()
    data.set_published(campaign['id'],result.json()['id'])
