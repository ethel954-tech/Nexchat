"""Custom Channels middleware helpers."""

from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from rest_framework.authtoken.models import Token


@database_sync_to_async
def _get_user_from_token(token_key):
    try:
        token = Token.objects.select_related('user').get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return None


class TokenAuthMiddleware(BaseMiddleware):
    """Populate scope['user'] from ?token=<key> query string."""

    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode()
        params = parse_qs(query_string)
        token_values = params.get('token')

        if token_values:
            token_user = await _get_user_from_token(token_values[0])
            if token_user is not None:
                scope['user'] = token_user

        return await super().__call__(scope, receive, send)
