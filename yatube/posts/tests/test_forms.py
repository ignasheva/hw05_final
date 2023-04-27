from http import HTTPStatus
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, Group, User


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
