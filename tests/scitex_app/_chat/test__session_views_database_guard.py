#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The error a host gets for mounting the session views without a database.

Django raised a bare `ImproperlyConfigured` here — "settings.DATABASES is
improperly configured. Please supply the ENGINE value." That names a SETTING
rather than the mistake, and reads as simply wrong to a host that emptied
DATABASES deliberately. 0.21.0 raises a subclass whose message says what was
mounted and what to mount instead.

WHAT THIS FILE DOES NOT CLAIM. None of this makes the mistake impossible. A
host can still mount `chat_urlpatterns` without a database; it now finds out
with a sentence that tells it what to do. Whether these views belong in this
SDK at all is a separate, open question and is not answered here.

SIBLING FILE: test__django_mount_points.py pins the shape of the two lists.
"""

from __future__ import annotations

import django
import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

if not settings.configured:
    settings.configure(
        DEFAULT_CHARSET="utf-8",
        ALLOWED_HOSTS=["*"],
        DATABASES={},
    )
    django.setup()

from django.test import RequestFactory  # noqa: E402

from scitex_app._chat._session_views import (  # noqa: E402
    ChatSessionsRequireADatabaseError,
    _database_is_configured,
    session_list_view,
)


def test_a_session_view_raises_the_NAMED_error():
    """Not Django's generic ImproperlyConfigured — the subclass, which is the
    only part of this a host can tell apart programmatically."""
    # Arrange
    request = RequestFactory().get("/api/chat/sessions/")
    # Act
    raised = pytest.raises(ChatSessionsRequireADatabaseError)
    # Assert
    with raised:
        session_list_view(request)


def test_the_named_error_is_still_an_ImproperlyConfigured():
    """This is what makes 0.21.0 additive rather than breaking. Django raised
    ImproperlyConfigured here before, so a host already catching it must keep
    working."""
    # Arrange
    # Act
    is_subclass = issubclass(ChatSessionsRequireADatabaseError, ImproperlyConfigured)
    # Assert
    assert is_subclass


def test_the_error_message_names_the_route_to_mount_instead():
    """A diagnosis that does not say what to do is just a louder 500. The
    message has to name the OTHER list, spelled the way a host would type it.

    Written without `pytest.raises` so this asserts once: the empty default
    means a view that did NOT raise fails here rather than passing quietly."""
    # Arrange
    request = RequestFactory().get("/api/chat/sessions/")
    # Act
    try:
        session_list_view(request)
        message = ""
    except ChatSessionsRequireADatabaseError as exc:
        message = str(exc)
    # Assert
    assert "chat_stream_urlpatterns" in message


def test_the_guard_can_also_say_YES_when_a_database_exists():
    """THE CONTROL, and without it every assertion above is satisfied by a
    guard hard-coded to refuse.

    `_database_is_configured` reads settings at call time, so pointing
    DATABASES at a real ENGINE asks the question in the other direction. This
    asserts the DETECTOR distinguishes the two configurations. It does NOT
    claim the session views work against a live database — that is a different
    test needing a real connection, and this one would pass without it."""
    # Arrange
    real = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
    # Act
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(settings, "DATABASES", real)
        says_configured = _database_is_configured()
    # Assert
    assert says_configured


def test_the_guard_says_NO_in_this_process():
    """The other direction of the same detector, and the precondition every
    assertion above depends on. `DATABASES={}` does not stay empty — Django
    fills in the DUMMY backend — so this is not the tautology it looks like."""
    # Arrange
    # Act
    says_configured = _database_is_configured()
    # Assert
    assert not says_configured


# EOF
