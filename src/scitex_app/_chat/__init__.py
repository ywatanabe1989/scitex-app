#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared chat module — LLM streaming for all SciTeX apps.

Provides:
- ChatBackend protocol for pluggable LLM providers
- SSE streaming utilities
- Django view that any app can mount
- Chat session models and CRUD views

``chat`` is exposed on the ``scitex_app`` package via a lazy
``__getattr__`` (PEP 562), not as a real importable submodule — so
``from scitex_app.chat import X`` raises ``ModuleNotFoundError``. Use
the bare ``from scitex_app import chat`` form (which does trigger the
package's ``__getattr__``), then attribute-access from there.

Usage (Django, REQUIRES A CONFIGURED DATABASE)::

    # urls.py
    from scitex_app import chat
    urlpatterns += chat.chat_urlpatterns

Usage (Django, NO DATABASE — streaming only)::

    # urls.py
    from scitex_app import chat
    urlpatterns += chat.chat_stream_urlpatterns

    # This is the correct mount for a host that configures no database,
    # `scitex_app.run_standalone` among them. Added in 0.21.0; before it,
    # `chat_urlpatterns` was the only list on offer and such a host had to
    # mount three routes it could not serve.

    # The session views (list / detail / messages) query ChatSession and
    # ChatMessage. Mounting them into settings with no DATABASES gives a
    # 500 per request, not a degraded mode — see _models.py.
    # `chat_stream_view` is the exception: it issues no ORM QUERY.
    #
    # "No query" is the claim, NOT "no import". Importing `_django` DOES
    # load `_models`, because `_django` imports `_session_views` at the
    # bottom to assemble `chat_urlpatterns`. That is harmless: defining a
    # model needs the app registry, not a connection. The distinction is
    # worth stating because import-reachability is the obvious proxy for
    # "needs a database" and it is the WRONG one — measured 2026-09-06,
    # when it contradicted a test written on that assumption.

Usage (WITHOUT DJANGO — no database involved)::

    from scitex_app import chat
    for event in chat.stream_chat("Hello", system_prompt="You are helpful."):
        print(event)

This second heading said "standalone" until 0.20.2, which was a third
meaning of that word in one package — here it meant "as a library", while
`scitex_app._standalone` is the DB-less launcher and `_models.py` used it
for single-user. Reserve "standalone" for the launcher.
"""

from ._protocol import ChatBackend
from ._stream import stream_chat
from ._sse import sse_format, sse_keepalive_wrap

__all__ = [
    "ChatBackend",
    "stream_chat",
    "sse_format",
    "sse_keepalive_wrap",
]


def __getattr__(name: str):
    """Lazy imports for optional Django integration."""
    if name == "chat_urlpatterns":
        from ._django import chat_urlpatterns

        return chat_urlpatterns
    if name == "chat_stream_urlpatterns":
        from ._django import chat_stream_urlpatterns

        return chat_stream_urlpatterns
    if name == "ChatSessionsRequireADatabaseError":
        from ._session_views import ChatSessionsRequireADatabaseError

        return ChatSessionsRequireADatabaseError
    if name == "chat_stream_view":
        from ._django import chat_stream_view

        return chat_stream_view
    # Session views
    if name == "session_list_view":
        from ._session_views import session_list_view

        return session_list_view
    if name == "session_detail_view":
        from ._session_views import session_detail_view

        return session_detail_view
    if name == "session_messages_view":
        from ._session_views import session_messages_view

        return session_messages_view
    # Models
    if name == "ChatSession":
        from ._models import ChatSession

        return ChatSession
    if name == "ChatMessage":
        from ._models import ChatMessage

        return ChatMessage
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
