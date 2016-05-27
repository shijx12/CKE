from django.conf.urls import include, url
import views

urlpatterns = [
    # Examples:
    # url(r'^$', 'cke.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^$', views.show_all_relation),
    url(r'^add_new_html/$', views.add_new_relation_html),
    url(r'^add_new/$', views.add_new_relation),

    url(r'^([^/]+?)/$', views.show_relation_iteration),
    url(r'^([^/]+?)/(\d+?)/$', views.show_iteration_content),
    # url(r'^([^/]+?)/(\d+?)/update_p/$', views.update_p),
    url(r'^([^/]+?)/remove_newest/$', views.remove_newest),
    url(r'^([^/]+?)/startcpl/$', views.start_cpl),
]