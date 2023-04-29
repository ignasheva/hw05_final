import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from http import HTTPStatus
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Post, Group, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug2',
            description='Тестовое описание 2'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)
        self.posts_count = Post.objects.count()

    def test_create_post(self):
        '''При отправке валидной формы создаётся новая запись в базе данных.'''
        form_data = {'text': self.post.text}
        response = self.authorized_client.post(
            reverse('posts:post_create'), data=form_data, follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        )
        self.assertEqual(Post.objects.count(), self.posts_count + 1)
        self.assertTrue(Post.objects.filter(text=self.post.text).exists())
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit(self):
        '''При отправке валидной формы, если пользователь авторизован,
          происходит изменение поста в базе данных.'''
        form_data = {'text': 'Редактируем пост', 'group': self.group2.id}
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=({self.post.id})),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        post = Post.objects.get(id=self.post.id)
        self.assertEqual(Post.objects.count(), self.posts_count)
        self.assertTrue(Post.objects.filter(text='Редактируем пост').exists())
        self.assertTrue(Post.objects.filter(group=self.group2.id).exists())
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(self.group.posts.count(), 0)
        self.assertEqual(self.group2.posts.count(), 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_by_guest_client(self):
        '''При отправке валидной формы, если пользователь неавторизован,
          не происходит изменение поста в базе данных.'''
        form_data = {'text': 'Редактируем пост', 'group': self.group.id}
        response = self.guest_client.post(
            reverse('posts:post_edit', args=({self.post.id})),
            data=form_data,
            follow=True,
        )
        path = f'/auth/login/?next=/posts/{self.post.id}/edit/'
        self.assertRedirects(response, path)
        self.assertEqual(Post.objects.count(), self.posts_count)
        self.assertFalse(Post.objects.filter(text='Редактируем пост').exists())
        self.assertEqual(response.status_code, HTTPStatus.OK)


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
