from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.core.paginator import Paginator
from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm
from django.urls import reverse


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    paginator = Paginator(post_list, 3)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    follower_count = Follow.objects.filter(user=author).count()
    following_count = Follow.objects.filter(author=author).count()
    try:
        following = Follow.objects.filter(user=request.user,
            author=author).count()
    except:
        following = False
    return render(
        request,
        'posts/profile.html',
        {'author': author, 'page': page, 'paginator': paginator,
        'following': following, 'follower_count': follower_count,
        'following_count': following_count}
        )


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    count = post.author.posts.count()
    form = CommentForm()
    items = Comment.objects.select_related('author',
        'post').filter(post_id=post_id)
    paginator = Paginator(items, 3)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'posts/post.html',
                    {'count': count, 'post': post,
                    'form': form, 'author': post.author,
                    'paginator': paginator, 'page': page,
                    'items': items}
    )


@login_required
def new_post(request):
    context = {'title': 'Новая запись', 'botton': 'Добавить'}
    if request.method != 'POST':
        form = PostForm()
        return render(request, 'posts/new_post.html',
            {'context': context, 'form': form}
        )
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if not form.is_valid():
        return render(request,
            'posts/new_post.html', {'context': context, 'form': form}
        )
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('index')


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    if request.user != post.author:
        return redirect('post', username=post.author.username, post_id=post_id)
    context = {'title': 'Редактировать запись',
        'botton': 'Сохранить',
        'post_id': post.id
    }
    form = PostForm(request.POST or None,
                    files=request.FILES or None, instance=post)
    if not form.is_valid():
        return render(request, 'posts/new_post.html',
            {'post': post, 'context': context, 'form': form}
        )
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect(f'/{post.author.username}/{post.id}')


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(
        Post, author__username=username, id=post_id)
    context = {'title': 'Редактировать запись',
               'botton': 'Сохранить',
               'post_id': post.id
               }
    form = CommentForm(request.POST or None)
    if not form.is_valid():
        return render(request, 'posts/comments.html',
                      {'post': post, 'context': context, 'form': form}
                      )
    comment = form.save(commit=False)
    comment.author = request.user
    comment.post = post
    comment.save()
    return redirect(reverse('post',
        kwargs={'username': username, 'post_id': post_id})
        )


def index(request):
    post = Post.objects.select_related('group').all()
    paginator = Paginator(post, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.post_group.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "group.html",
                  {'group': group, 'page': page, 'paginator': paginator}
                  )


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def follow_index(request):
    post = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'posts/follow.html',
        {'page': page, 'paginator': paginator})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=request.user, author=author).exists()
    if request.user.username != username and not follow:
        Follow.objects.create(user=request.user, author=author)
    return redirect('follow_index')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=request.user, author=author)
    follow.delete()
    return redirect('follow_index')
