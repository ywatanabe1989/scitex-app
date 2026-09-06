#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The SECOND requirement of the session views: their app must be installed.

0.21.0 shipped a guard that asked one question — is a database configured —
and a message saying these views "require a configured database". True, and
not the whole requirement. `ChatSession` and `ChatMessage` declare an EXPLICIT
`app_label`, so Django builds the model classes without consulting
INSTALLED_APPS and resolves the app only at QUERY time. A host with a real
database and no registration therefore passes the 0.21.0 guard and fails
deeper down with a LookupError about an app label — precisely the confusing
error 0.21.0 existed to remove, surviving in a different configuration.

WHY THE EXPLICIT app_label MATTERS, since it is the whole reason this is not
caught earlier: without one, Django raises when the model class is created and
the failure is loud at import. With one, nothing complains until a query runs.
That difference is what made the case reachable, and it is why "models with no
installed app blow up at import" — a true rule — did not apply here.

MEASURED, not hypothetical (scitex-hub, 2026-09-06): hub installs
`figrecipe._django`, which loads that module's DEFAULT AppConfig, while the
config registering these models is a SECOND AppConfig in the same module. One
INSTALLED_APPS entry loads one config.
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
        INSTALLED_APPS=["django.contrib.contenttypes"],
    )
    django.setup()

from django.test import RequestFactory  # noqa: E402

from scitex_app._chat._models import ChatSession  # noqa: E402
from scitex_app._chat._session_views import (  # noqa: E402
    ChatSessionsAppNotInstalledError,
    ChatSessionsRequireADatabaseError,
    ChatSessionsUnavailableError,
    _app_is_installed,
    session_list_view,
)

_REAL_DB = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}


def _get():
    return RequestFactory().get("/api/chat/sessions/")


# ------------------------------------------------------- the detector


def test_the_models_app_is_NOT_installed_in_this_process():
    """The precondition every assertion below depends on, asserted rather than
    assumed — the tests would pass vacuously against a process that happened
    to register it."""
    # Arrange
    # Act
    installed = _app_is_installed(ChatSession._meta.app_label)
    # Assert
    assert not installed


def test_the_detector_can_also_say_YES():
    """THE CONTROL. Every assertion here is equally satisfied by a detector
    hard-coded to return False, which would also make the new guard fire
    permanently. `contenttypes` is really in this process's INSTALLED_APPS, so
    this asks the same function the other way."""
    # Arrange
    # Act
    installed = _app_is_installed("contenttypes")
    # Assert
    assert installed


# ------------------------------------------------------- the guard


def test_a_database_alone_is_not_enough():
    """The case 0.21.0 missed. With a real ENGINE configured the database
    requirement is met, so anything raised here is the SECOND requirement
    speaking."""
    # Arrange
    request = _get()
    # Act
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(settings, "DATABASES", _REAL_DB)
        raised = pytest.raises(ChatSessionsAppNotInstalledError)
        # Assert
        with raised:
            session_list_view(request)


def test_the_message_names_the_label_that_is_missing():
    """A host cannot register an app whose label the error will not name."""
    # Arrange
    request = _get()
    message = ""
    # Act
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(settings, "DATABASES", _REAL_DB)
        try:
            session_list_view(request)
        except ChatSessionsAppNotInstalledError as exc:
            message = str(exc)
    # Assert
    assert ChatSession._meta.app_label in message


def test_with_NO_database_the_database_error_wins():
    """THE CONTROL for the test above, and the reason the two errors are
    separate classes. Both requirements fail in this process; if the guard
    reported the app every time, the DB case would silently vanish and a
    standalone host would be told to fix INSTALLED_APPS instead of its
    database."""
    # Arrange
    request = _get()
    # Act
    raised = pytest.raises(ChatSessionsRequireADatabaseError)
    # Assert
    with raised:
        session_list_view(request)


# ------------------------------------------------------- the hierarchy


def test_both_failures_share_one_base_to_catch():
    """A host asking "can these views work here" should not have to enumerate
    the requirements."""
    # Arrange
    both = (ChatSessionsRequireADatabaseError, ChatSessionsAppNotInstalledError)
    # Act
    all_covered = all(issubclass(e, ChatSessionsUnavailableError) for e in both)
    # Assert
    assert all_covered


def test_the_base_is_still_an_ImproperlyConfigured():
    """What keeps this additive: Django raised ImproperlyConfigured here before
    0.21.0, and 0.21.0's own subclass did too. A host catching either keeps
    working."""
    # Arrange
    # Act
    is_subclass = issubclass(ChatSessionsUnavailableError, ImproperlyConfigured)
    # Assert
    assert is_subclass


# EOF
