#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The DB-free claim about `chat_stream_view`, pinned by behaviour.

0.20.2 asserts in three docstrings that `chat_stream_view` issues no ORM query
and is safe to mount without a database, while the session views are not.
Nothing checked it — §7 prefers a mechanical barrier to a written warning, and
what shipped was three written warnings.

WHY THE OBVIOUS GUARD IS NOT HERE. The natural test is "importing `_django`
never loads `_models`". It was written, RUN, and DISPROVED on 2026-09-06:
`_django` imports `_session_views` at the bottom to assemble
`chat_urlpatterns`, so the import DOES reach the models. Harmless — defining a
model needs the app registry, not a connection — but it means
import-reachability cannot express this claim. A grep cannot either: the
paragraph EXPLAINING this rule raised `__init__.py` from 6 "ORM references" to
8, because docstring prose counts.

So the claim is about QUERIES, and only calling the views can ask about
queries.

PROVENANCE: figrecipe measured the real thing on their editor — with no
DATABASES configured, `GET /api/chat/sessions/` answered 500 with a Django
settings diagnostic, while `POST /api/chat/stream` returned 200 and streamed,
with and without `session_id`, failing only on a missing API key. This file is
that measurement, reproduced where it can regress.
"""

from __future__ import annotations

import json

import django
import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

# DATABASES={} is Django's dummy backend — the condition figrecipe's standalone
# runs in, and the one `scitex_app._standalone` configures. Not a simulation of
# a missing database; it IS the missing database.
if not settings.configured:
    settings.configure(
        DEFAULT_CHARSET="utf-8",
        ALLOWED_HOSTS=["*"],
        DATABASES={},
        # One real app, so "is this label installed" can be asked in BOTH
        # directions. Identical in every _chat test module: Django configures
        # settings once per process and the module order is not ours to
        # choose, so the blocks must agree or the fixture depends on luck.
        INSTALLED_APPS=["django.contrib.contenttypes"],
    )
    django.setup()

from django.test import RequestFactory  # noqa: E402

from scitex_app._chat._django import chat_stream_view  # noqa: E402
from scitex_app._chat._session_views import session_list_view  # noqa: E402


def _database_is_absent() -> bool:
    """Is this process actually running without a usable database?"""
    default = (getattr(settings, "DATABASES", None) or {}).get("default") or {}
    engine = default.get("ENGINE") or ""
    return not engine or engine.endswith("dummy")


def _post(payload: dict):
    return RequestFactory().post(
        "/api/chat/stream",
        data=json.dumps(payload),
        content_type="application/json",
    )


def test_this_process_really_has_no_database():
    """THE PRECONDITION, asserted rather than assumed.

    Every assertion below is vacuous if some other test module configured
    Django with a real database first — "did not raise ImproperlyConfigured"
    passes trivially when a connection exists. Django settings are configured
    once per process and the order is not ours to control, so the condition has
    to be checked rather than trusted."""
    # Arrange
    # Act
    absent = _database_is_absent()
    # Assert
    assert absent


def test_the_stream_view_does_not_hit_the_database():
    """The claim three docstrings make. A missing API key, a backend error or a
    503 are all ACCEPTABLE here — they are different, correct failures. Only
    ImproperlyConfigured means this view reached for a database."""
    # Arrange
    request = _post({"prompt": "hello"})
    # Act
    raised_db_error = False
    try:
        chat_stream_view(request)
    except ImproperlyConfigured:
        raised_db_error = True
    except Exception:
        raised_db_error = False
    # Assert
    assert not raised_db_error


def test_passing_a_session_id_still_does_not_hit_the_database():
    """The half of the claim with the least evidence behind it, and the one a
    future change is most likely to break: `session_id` is exactly the argument
    that LOOKS like it should cause a session lookup. figrecipe measured that
    it does not."""
    # Arrange
    request = _post({"prompt": "hello", "session_id": 1})
    # Act
    raised_db_error = False
    try:
        chat_stream_view(request)
    except ImproperlyConfigured:
        raised_db_error = True
    except Exception:
        raised_db_error = False
    # Assert
    assert not raised_db_error


def test_a_session_view_DOES_hit_the_database():
    """THE CONTROL, and without it the two tests above prove nothing.

    "Did not raise ImproperlyConfigured" is satisfied by a view that was never
    reached, by a dummy backend that does not actually refuse, and by a
    RequestFactory that failed before dispatch. This asserts the same setup CAN
    produce the error — so the absence above is evidence rather than silence."""
    # Arrange
    request = RequestFactory().get("/api/chat/sessions/")
    # Act
    raised = pytest.raises(ImproperlyConfigured)
    # Assert
    with raised:
        session_list_view(request)


# EOF
