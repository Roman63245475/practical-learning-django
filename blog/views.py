from django.shortcuts import render, get_object_or_404
from .models import Post, Comment
from django.core.paginator import Paginator
from .forms import EmailPostForm, CommentForm, SearchForm
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.http import require_POST
from taggit.models import Tag
from django.db.models import Count
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank


def post_list(request, tag_slug=None):
    list_of_posts = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        list_of_posts = list_of_posts.filter(tags__in=[tag])

    paginator = Paginator(list_of_posts, 3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'blog/post/list.html', {'page_obj': page_obj, 'tag': tag})


def post_detail(request, year, month, day, post_slug):
    post = get_object_or_404(Post, slug=post_slug,
                             status=Post.Status.PUBLISHED,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)

    comments = post.comments.filter(active=True)
    form = CommentForm()
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.all().filter(tags__in=post_tags_ids).exclude(pk=post.pk)
    sorted_similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]
    context = {'post': post,
               'comments': comments,
               'form': form,
               'similar_posts': sorted_similar_posts, }
    return render(request, 'blog/post/detail.html', context=context)


def post_share(request, post_slug):
    post = get_object_or_404(Post, slug=post_slug)
    sent = False
    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you to read {post.title}"
            message = f"Read {post.title} at {post_url}\n\n"
            send_mail(subject, message, settings.EMAIL_HOST_USER, [cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'form': form, 'post': post, 'sent': sent})


@require_POST
def post_comment(request, post_slug):
    post = get_object_or_404(Post, slug=post_slug)
    comment = None
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()

    return render(request, 'blog/post/comment.html', {'post': post, 'form': form, 'comment': comment})


def post_search(request):
    form = SearchForm()
    query = None
    results = []

    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            search_vector = SearchVector('title', weight='A') + SearchVector('body', weight='B')
            search_query = SearchQuery(query)
            results = Post.published.annotate(search=search_vector, rank=SearchRank(search_vector, search_query)).filter(rank__gte=0.3).order_by('-rank')

    return render(request, 'blog/post/search.html', {'form': form, 'query': query, 'results': results})
