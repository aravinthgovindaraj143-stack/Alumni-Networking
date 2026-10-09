"""
ASGI config for myproject project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django_asgi_application = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from accounts.routing import websocket_urlpatterns

application = ProtocolTypeRouter(
	{
		"http": django_asgi_application,
		"websocket": AuthMiddlewareStack(
			URLRouter(websocket_urlpatterns)
		),
	}
)
