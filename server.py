"""
Development server uvicorn
Production server:
    1)-w cpu count * 2 + 1
    2)--preload обязательно иначе set_webhook будет повторятся для каждого worker
    gunicorn config.asgi:application -w 9 -k uvicorn.streams.UvicornWorker --preload -b "0.0.0.0:8000"
TODO:
    написать systemd service для gunicorn
"""
import uvicorn


if __name__ == '__main__':
    uvicorn.run("config.asgi:application", host='0.0.0.0', reload=True, lifespan='off')

