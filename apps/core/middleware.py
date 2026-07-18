from django.http import HttpResponseForbidden
from django.middleware.csrf import get_token


class EnsureCsrfCookieMiddleware:
    """
    Ensures CSRF cookie is set on safe requests.
    Helps prevent CSRF token mismatch on auth forms.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Touch CSRF token early so CsrfViewMiddleware can set cookie
        if request.method in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            get_token(request)
        return self.get_response(request)


class DisableRightClickMiddleware:
    SCRIPT_MARKER = b'no-context-menu-guard'
    SCRIPT = b"""
<script id="no-context-menu-guard">
(function () {
  'use strict';
  if (window.__CIET_NO_CONTEXT_MENU__) return;
  window.__CIET_NO_CONTEXT_MENU__ = true;

  document.addEventListener('contextmenu', function (event) {
    event.preventDefault();
    alert('Sorry ! Right Click No Access.');
  }, true);
})();
</script>
"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Right-click blocking disabled — pass through without modification
        return self.get_response(request)


class SiteThemeMiddleware:
    STYLE_MARKER = b'site-theme-css'
    SCRIPT_MARKER = b'site-theme-js'
    VANTA_STUB_MARKER = b'ciet-vanta-stub'
    STYLE = b'<link id="site-theme-css" href="/static/css/site_theme.css?v=4" rel="stylesheet">'
    SCRIPT = b'<script id="site-theme-js" src="/static/js/site_theme.js?v=2"></script>'
    VANTA_STUB = b'<script id="ciet-vanta-stub">window.VANTA=window.VANTA||{FOG:function(){return null;}};</script>'
    HEAVY_BACKGROUND_SCRIPTS = (
        b'<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r134/three.min.js"></script>',
        b'<script src="https://cdn.jsdelivr.net/npm/vanta@latest/dist/vanta.fog.min.js"></script>',
    )

    EXCLUDED_PATHS = {'/'}
    EXCLUDED_PREFIXES = ('/static/', '/media/', '/api/', '/faculty-portal/', '/faculty/', '/student/')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if self._should_skip(request, response):
            return response

        content = response.content
        lower_content = content.lower()
        content = self._remove_heavy_background_scripts(content)
        lower_content = content.lower()

        content = self._add_body_class(content, lower_content)
        lower_content = content.lower()

        head_index = lower_content.rfind(b'</head>')
        if head_index != -1 and self.STYLE_MARKER not in content:
            content = content[:head_index] + self.STYLE + self.VANTA_STUB + content[head_index:]
            lower_content = content.lower()

        body_index = lower_content.rfind(b'</body>')
        if body_index != -1 and self.SCRIPT_MARKER not in content:
            content = content[:body_index] + self.SCRIPT + content[body_index:]

        response.content = content
        if response.has_header('Content-Length'):
            response['Content-Length'] = str(len(response.content))
        return response

    def _remove_heavy_background_scripts(self, content):
        for script in self.HEAVY_BACKGROUND_SCRIPTS:
            content = content.replace(script, b'')
        return content

    def _should_skip(self, request, response):
        content_type = response.get('Content-Type', '')
        return (
            request.path in self.EXCLUDED_PATHS
            or request.path.startswith(self.EXCLUDED_PREFIXES)
            or response.status_code != 200
            or 'text/html' not in content_type
            or getattr(response, 'streaming', False)
            or not hasattr(response, 'content')
        )

    def _add_body_class(self, content, lower_content):
        body_index = lower_content.find(b'<body')
        if body_index == -1 or b'ciet-site-theme' in content:
            return content

        tag_end = content.find(b'>', body_index)
        if tag_end == -1:
            return content

        body_tag = content[body_index:tag_end]
        lower_body_tag = body_tag.lower()
        class_index = lower_body_tag.find(b'class=')

        if class_index == -1:
            return content[:tag_end] + b' class="ciet-site-theme"' + content[tag_end:]

        quote_index = class_index + len(b'class=')
        quote = body_tag[quote_index:quote_index + 1]
        if quote not in (b'"', b"'"):
            return content

        class_start = quote_index + 1
        class_end = body_tag.find(quote, class_start)
        if class_end == -1:
            return content

        absolute_class_end = body_index + class_end
        return content[:absolute_class_end] + b' ciet-site-theme' + content[absolute_class_end:]


class RoleMiddleware:
    ROLE_URL_MAP = {
        '/faculty/':       ['HOD', 'Mentor', 'Faculty'],
        '/students/':      ['Director', 'HOD', 'Mentor', 'Faculty', 'Examcell'],
        '/student/':       ['Student', 'HOD', 'Mentor', 'Faculty', 'Examcell'],
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return self.get_response(request)
            for prefix, roles in self.ROLE_URL_MAP.items():
                if request.path.startswith(prefix):
                    if request.user.role not in roles:
                        return HttpResponseForbidden('Access Denied')
        return self.get_response(request)
