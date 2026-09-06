#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The two chat mount points published by `_django.py`.

0.21.0 splits the single `chat_urlpatterns` into a database-free subset
(`chat_stream_urlpatterns`) and the full list. Until then the full list was the
only one on offer, and it bundles the DB-free streaming route with three
session CRUD routes that every one query the ORM — so a host configuring no
database, `scitex_app.run_standalone` among them, had nothing correct to mount.

SIBLING FILES:
    test__django_db_free.py               the stream view issues no ORM query
    test__session_views_database_guard.py the error for mounting the wrong one

All three configure the same DATABASES={} process condition, so they agree
whichever runs first.
"""

from __future__ import annotations

import json

import django
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

from scitex_app._chat._django import (  # noqa: E402
    chat_stream_urlpatterns,
    chat_urlpatterns,
)


def _route_names(patterns) -> set[str]:
    return {p.name for p in patterns}


def test_the_stream_mount_is_a_subset_of_the_full_mount():
    """The two lists must not drift. `chat_urlpatterns` is BUILT from the
    stream list rather than repeating its route, and this is what says so — a
    later edit that redefines the stream route in only one place fails here."""
    # Arrange
    # Act
    only_in_subset = _route_names(chat_stream_urlpatterns) - _route_names(
        chat_urlpatterns
    )
    # Assert
    assert only_in_subset == set()


def test_the_stream_mount_carries_no_session_route():
    """The entire point of the smaller list: a host with no database can mount
    it and get nothing that queries the ORM."""
    # Arrange
    # Act
    names = _route_names(chat_stream_urlpatterns)
    # Assert
    assert not any("session" in name for name in names)


def test_the_full_mount_DOES_carry_session_routes():
    """THE CONTROL for the test above, which would also pass if `session` were
    the wrong word to look for, or if both lists were empty."""
    # Arrange
    # Act
    names = _route_names(chat_urlpatterns)
    # Assert
    assert any("session" in name for name in names)


def test_every_route_in_the_stream_mount_survives_with_no_database():
    """The claim the smaller list makes, asserted over the POPULATION rather
    than over `chat_stream_view` by name — a route added to this list later is
    covered without anyone remembering to add a test.

    Any other exception is acceptable: a missing API key or a backend error are
    different, correct failures. Only ImproperlyConfigured means the route
    reached for a database."""
    # Arrange
    reached_for_a_database = []
    # Act
    for route in chat_stream_urlpatterns:
        request = RequestFactory().post(
            "/" + str(route.pattern),
            data=json.dumps({"prompt": "hello"}),
            content_type="application/json",
        )
        try:
            route.callback(request)
        except ImproperlyConfigured:
            reached_for_a_database.append(route.name)
        except Exception:
            pass
    # Assert
    assert reached_for_a_database == []


# EOF
