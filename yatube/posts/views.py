from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Post, Group, Comment, Follow, User
from .forms import PostForm, CommentForm


LIMIT_ELEMENT = 10


def paginator_func(request, posts):
    '''Добавить пагинацию на страницу.'''
    paginator = Paginator(posts, LIMIT_ELEMENT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    '''Вернуть главную страницу.'''
    template = 'posts/index.html'
    title = 'Последние обновления на сайте'
    posts = Post.objects.all()
    page_obj = paginator_func(request, posts)
    context = {
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    '''Вернуть страницу группы.'''
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    title = f'Записи сообщества {group}'
    posts = group.posts.all()
    page_obj = paginator_func(request, posts)
    context = {
        'title': title,
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    '''Вернуть страницу профиля.'''
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    title = f'Профайл пользователя {author}'
    posts = author.posts.all()
    counter = posts.count()
    page_obj = paginator_func(request, posts)
    context = {
        'title': title,
        'author': author,
        'counter': counter,
        'page_obj': page_obj,
    }
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            author=author, user=request.user
        ).exists()
        context['following'] = following
    return render(request, template, context)


def post_detail(request, post_id):
    '''Вернуть страницу отдельного поста.'''
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post.objects.select_related('author'), pk=post_id)
    author_posts_count = Post.objects.filter(author__pk=post.author.pk).count()
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post=post)
    context = {
        'post': post,
        'author_posts_count': author_posts_count,
        'form': form,
        'comments': comments
    }
    return render(request, template, context)


@login_required
def post_create(request):
    '''Создать новый пост.'''
    template = 'posts/create_post.html'
    title = 'Новый пост'
    form = PostForm(request.POST or None, files=request.FILES or None)
    context = {
        'title': title,
        'form': form,
        'username': request.user,
    }
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=post.author)
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    '''Редактировать пост.'''
    template = 'posts/create_post.html'
    title = 'Редактирование записи'
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post.id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post.id)
    context = {
        'title': title,
        'is_edit': True,
        'form': form,
        'post': post,
        }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    '''Добавить комментарий.'''
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    '''Показать посты авторов, за которыми следит текущий пользователь.'''
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = paginator_func(request, posts)
    title = 'Избранные посты'
    template = 'posts/follow.html'
    context = {
        'title': title,
        'page_obj': page_obj
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    '''Подписаться на автора.'''
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    '''Отписаться от автора.'''
    author = get_object_or_404(User, username=username)
    Follow.objects.get(user=request.user, author=author).delete()
    return redirect('posts:follow_index')
