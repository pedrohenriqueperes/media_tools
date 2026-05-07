from django.http import HttpResponse
from django.urls import reverse


def robots_txt(request):
    base = request.build_absolute_uri('/').rstrip('/')
    content = f"""User-agent: *
Allow: /
Disallow: /dashboard/
Disallow: /submit/
Disallow: /job/
Disallow: /admin/
Disallow: /accounts/social/

Sitemap: {base}/sitemap.xml
"""
    return HttpResponse(content, content_type='text/plain')


def sitemap_xml(request):
    base = request.build_absolute_uri('/').rstrip('/')
    urls = [
        {'loc': f'{base}/', 'changefreq': 'weekly', 'priority': '1.0'},
        {'loc': f'{base}{reverse("account_signup")}', 'changefreq': 'monthly', 'priority': '0.8'},
        {'loc': f'{base}{reverse("account_login")}', 'changefreq': 'monthly', 'priority': '0.5'},
    ]
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        parts.append(
            f'  <url>\n'
            f'    <loc>{u["loc"]}</loc>\n'
            f'    <changefreq>{u["changefreq"]}</changefreq>\n'
            f'    <priority>{u["priority"]}</priority>\n'
            f'  </url>'
        )
    parts.append('</urlset>')
    return HttpResponse('\n'.join(parts), content_type='application/xml')
