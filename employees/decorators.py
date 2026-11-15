"""Reusable view decorators for SkillBridge EMS.

Each decorator runs code BEFORE the view (check something, log the attempt,
count a request) and/or AFTER it (log the outcome, change the response), so
that code is written once and reused instead of being copied into every view.

They work on plain function views. For class-based views, wrap them with
Django's ``method_decorator`` (see employees/views.py for examples).
"""
import functools
import logging
import time

from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.utils.cache import add_never_cache_headers, patch_cache_control

audit_logger = logging.getLogger('employees.audit')


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:                                   # behind Render's proxy
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


def _who(request):
    user = getattr(request, 'user', None)
    if user is not None and user.is_authenticated:
        return user.username
    return 'anonymous'


def audit_action(action):
    """BEFORE: log who tried to do what. AFTER: log the outcome and how long it took.

    Records the user, IP address, HTTP method, path, status code and duration.
    Refused requests (403/404) are logged as warnings, and unexpected errors
    are logged with a traceback and then re-raised so Django still handles them.
    Nothing sensitive (salary, email, form data) is ever written to the log.
    """
    def decorator(view):
        @functools.wraps(view)
        def wrapper(request, *args, **kwargs):
            who, ip = _who(request), _client_ip(request)
            audit_logger.info("AUDIT start | action=%s | user=%s | ip=%s | %s %s",
                              action, who, ip, request.method, request.path)
            started = time.monotonic()
            try:
                response = view(request, *args, **kwargs)
            except (PermissionDenied, Http404) as error:
                audit_logger.warning("AUDIT refused | action=%s | user=%s | ip=%s | reason=%s",
                                     action, who, ip, type(error).__name__)
                raise
            except Exception:
                audit_logger.exception("AUDIT error | action=%s | user=%s | ip=%s",
                                       action, who, ip)
                raise
            elapsed = time.monotonic() - started
            status = getattr(response, 'status_code', 0)
            level = logging.WARNING if status >= 400 else logging.INFO
            audit_logger.log(level, "AUDIT done | action=%s | user=%s | status=%s | %.3fs",
                             action, who, status, elapsed)
            return response
        return wrapper
    return decorator


def rate_limit(scope, calls=30, period=60):
    """BEFORE: allow at most ``calls`` requests per ``period`` seconds per user.

    Stops a runaway script or a stuck button from hammering a data-changing
    view. Anonymous visitors are counted by IP address. Over the limit, the
    view is not run at all and the client gets 429 Too Many Requests.

    The counter lives in Django's cache, so with LocMemCache it is per server
    process. A shared cache such as Redis is needed to enforce it across workers.
    """
    def decorator(view):
        @functools.wraps(view)
        def wrapper(request, *args, **kwargs):
            user = getattr(request, 'user', None)
            if user is not None and user.is_authenticated:
                ident = f'user{user.pk}'
            else:
                ident = f'ip{_client_ip(request)}'
            key = f'ratelimit:{scope}:{ident}'
            cache.add(key, 0, timeout=period)       # starts the window only if it is not running
            try:
                count = cache.incr(key)
            except ValueError:                      # key expired between add and incr
                cache.set(key, 1, timeout=period)
                count = 1
            if count > calls:
                audit_logger.warning("AUDIT rate-limited | scope=%s | user=%s | ip=%s",
                                     scope, _who(request), _client_ip(request))
                response = HttpResponse('Too many requests. Please wait a moment and try again.',
                                        status=429, content_type='text/plain')
                response['Retry-After'] = str(period)
                return response
            return view(request, *args, **kwargs)
        return wrapper
    return decorator


def no_store(view):
    """AFTER: change the response so browsers and proxies never keep a copy.

    Used on pages that show salary, so the data is not left in a shared cache
    or shown again from the browser's back button after logging out.
    """
    @functools.wraps(view)
    def wrapper(request, *args, **kwargs):
        response = view(request, *args, **kwargs)
        add_never_cache_headers(response)
        patch_cache_control(response, no_store=True, private=True)
        return response
    return wrapper
