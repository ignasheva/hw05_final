import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from ..models import Post, Group, Comment, Follow, User


LIMIT_ELEMENT = 10
SECOND_LIMIT_ELEMENT = 3
NUMBER_OF_POSTS = 13
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create(username='StasBasov')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.another_user = User.objects.create(username='AnotherUser')

    def setUp(self):
        '''Подготовка прогона теста. Вызывается перед каждым тестом.'''
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    def test_pages_uses_correct_template(self):
        '''URL-адрес использует соответствующий шаблон.'''
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.post.author}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            ): 'posts/create_post.html',

        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        '''Шаблон index сформирован с правильным контекстом.'''
        response = self.guest_client.get(reverse('posts:index'))
        expected = list(Post.objects.all()[:LIMIT_ELEMENT])
        self.assertEqual(list(response.context['page_obj']), expected)

    def test_group_list_page_show_correct_context(self):
        '''Шаблон group_list сформирован с правильным контекстом.'''
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        expected = list(self.group.posts.all()[:LIMIT_ELEMENT])
        self.assertEqual(list(response.context['page_obj']), expected)

    def test_profile_page_show_correct_context(self):
        '''Шаблон profile сформирован с правильным контекстом.'''
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': self.post.author})
        )
        expected = list(self.user.posts.all()[:LIMIT_ELEMENT])
        self.assertEqual(list(response.context['page_obj']), expected)

    def test_post_detail_page_show_correct_context(self):
        '''Шаблон post_detail сформирован с правильным контекстом.'''
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').author, self.post.author)
        self.assertEqual(response.context.get('post').group, self.post.group)

    def test_create_page_show_correct_context(self):
        '''Шаблон create сформирован с правильным контекстом.'''
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_edit_page_show_correct_context(self):
        '''Шаблон create_edit сформирован с правильным контекстом.'''
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_check_group_in_pages(self):
        '''При указании группы, происходит создание поста
        на страницах index/group_list/profile.'''
        form_fields = {
            reverse('posts:index'): Post.objects.get(group=self.post.group),
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): Post.objects.get(group=self.post.group),
            reverse(
                'posts:profile', kwargs={'username': self.post.author}
            ): Post.objects.get(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.guest_client.get(value)
                form_field = response.context['page_obj']
                self.assertIn(expected, form_field)

    def test_check_group_not_in_wrong_group_list_page(self):
        '''Проверяем, что пост не попал в группу,
        для которой не был предназначен.'''
        form_fields = {
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): Post.objects.exclude(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.guest_client.get(value)
                form_field = response.context['page_obj']
                self.assertNotIn(expected, form_field)

    def test_comment_show_correct_context(self):
        '''Проверяем, что комментировать пост может
        только авторизованный пользователь.
        Комментарий отображается на странице поста.'''
        comments_count = Comment.objects.count()
        form_data = {'text': 'Тестовый комментарий'}
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(text='Тестовый комментарий').exists()
        )

    def test_check_cache(self):
        '''Проверка работы кеша.'''
        response = self.guest_client.get(reverse('posts:index'))
        first_content = response.content
        Post.objects.get(id=1).delete()
        response2 = self.guest_client.get(reverse('posts:index'))
        second_content = response2.content
        self.assertEqual(first_content, second_content)

    def test_follow_page(self):
        '''Проверяем возможность подписки и отписки,
        когда пользователь авторизован.
        Отображение нового поста у подписчиков.'''
        response = self.authorized_client.get(reverse('posts:follow_index'))
        empty_page = response.context['page_obj']
        self.assertEqual(len(empty_page), 0)
        # Подписаться на автора
        Follow.objects.get_or_create(user=self.user, author=self.post.author)
        response2 = self.authorized_client.get(reverse('posts:follow_index'))
        page = response2.context['page_obj']
        self.assertEqual(len(page), 1)
        self.assertIn(self.post, page)
        # У не подписанного пользователя не отображается новый пост автора
        self.authorized_client.force_login(self.another_user)
        response3 = self.authorized_client.get(reverse('posts:follow_index'))
        page = response3.context['page_obj']
        self.assertNotIn(self.post, page)
        # Отписаться от автора
        Follow.objects.all().delete()
        response4 = self.authorized_client.get(reverse('posts:follow_index'))
        empty_page = response4.context['page_obj']
        self.assertEqual(len(empty_page), 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        post_list = []
        for i in range(NUMBER_OF_POSTS):
            cls.user = User.objects.create(username=f'HasNoName{i}')
            cls.group = Group.objects.create(
                title=f'Тестовая группа{i}',
                slug=f'test-slug{i}',
                description=f'Тестовое описание{i}',
            )
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост{i}',
                group=cls.group,
            )
            post_list.append(cls)

    def setUp(self):
        '''Подготовка прогона теста. Вызывается перед каждым тестом.'''
        self.guest_client = Client()

    def test_first_page_contains_ten_records(self):
        '''Проверка: количество постов на первой странице равно 10.'''
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), LIMIT_ELEMENT)

    def test_second_page_contains_three_records(self):
        '''Проверка: на второй странице должно быть три поста.'''
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(
            response.context['page_obj']
        ), SECOND_LIMIT_ELEMENT)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='NoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()

    def test_image_in_index_profile_and_group_list_pages(self):
        '''Картинка передается на страницы index, profile, group_list.'''
        templates = (
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': self.post.author}),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
        )
        for url_name in templates:
            with self.subTest(url_name):
                response = self.guest_client.get(url_name)
                item = response.context['page_obj'][0]
                self.assertEqual(item.image, self.post.image)

    def test_image_in_post_detail_page(self):
        '''Картинка передается на страницу post_detail.'''
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
        )
        item = response.context['post']
        self.assertEqual(item.image, self.post.image)

    def test_image_in_database(self):
        '''Пост с картинкой создается в БД'''
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост', image='posts/small.gif'
            ).exists()
        )
