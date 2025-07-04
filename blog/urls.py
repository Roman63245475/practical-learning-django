from django.urls import path
from .views import *
from .feeds import LatestPostsFeed

app_name = 'blog'

urlpatterns = [
    path('', post_list, name='post_list'),
    path('<int:year>/<int:month>/<int:day>/<slug:post_slug>', post_detail, name='post_detail'),
    path('share/<slug:post_slug>', post_share, name='post_share'),
    path('comment/<slug:post_slug>', post_comment, name='post_comment'),
    path('tag/<slug:tag_slug>', post_list, name='posts_by_tag'),
    path('feeds/', LatestPostsFeed(), name='post_feed'),
    path('search/', post_search, name='post_search'),
]