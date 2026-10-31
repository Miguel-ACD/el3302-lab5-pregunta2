"""Genera archivos fuera del proceso web para evitar errores de tiempo."""
import time
from . import data, logic
from . import instagram


def main():
    data.init()
    while True:
        job=data.next_job()
        if job is not None:
            try:
                logic.make_media(data.get(job))
                data.set_status(job,'ready')
            except Exception as exc:
                data.set_status(job,'error',str(exc)[:300])
        publish=data.next_publish()
        if publish:
            try:
                instagram.publish(data.get(publish))
            except Exception as exc:
                data.set_status(publish,'publish_error',str(exc)[:300])
        if job is None and publish is None:
            time.sleep(2)


if __name__=='__main__': main()
