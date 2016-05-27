from django.conf.urls import include, url
from django.contrib import admin
# from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    # Examples:
    # url(r'^$', 'cke.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^category/', include('category.urls')),
    url(r'^relation/', include('relation.urls')),
]

urlpatterns += staticfiles_urlpatterns()