from django.test import TestCase
from django.test import Client
from posts.models import Post, Group, User, Comment, Follow
from django.urls import reverse
import tempfile as tempfile
from django.test.utils import override_settings
import io
from PIL import Image
from django.core.cache import cache
from django.core.files.base import ContentFile


class TestPosts(TestCase):
    def setUp(self):
        self.group1 = Group.objects.create(
            title='testGroup1',
            slug='test_slug1',
            description='описание группы1'
        )
        self.client_on = Client()
        self.client_on_2 = Client()
        self.client_off = Client()
        self.user = User.objects.create(
            username='test_user', email='q@q.com')
        self.user.set_password('123')
        self.user.save()
        self.user_2 = User.objects.create(
            username='test_user2', email='q2@q.com')
        self.user_2.set_password('1234')
        self.user_2.save()
        self.client_on.force_login(self.user)
        self.client_on_2.force_login(self.user_2)
        self.clients = (self.client_on, self.client_off,)

    def _get_url(self):
        return {
            'index':
                reverse('index'),
            'profile':
                reverse('profile', kwargs={'username': self.user.username}),
            'post':
                reverse('post',
                        kwargs={
                            'username': self.post.author,
                            'post_id': self.post.id
                        })
        }

    def test_new_post_user_on(self):
        """
        Проверка, что зарегистрированный пользователь может создать пост
        """
        check_list = {'text': 'test text',
            'group': self.group1.id,
            'author': self.user.id
        }
        response = self.client_on.post(
            reverse('new_post'),
            data={
                'text': check_list['text'],
                'group': check_list['group']
            }
        )
        self.assertRedirects(response,
            expected_url=reverse('index'),
            status_code=302,
            target_status_code=200,
            msg_prefix='',
            fetch_redirect_response=True
        )
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.select_related('group', 'author').first()
        self.assertEqual(post.text, check_list['text'])
        self.assertEqual(post.group, self.group1)
        self.assertEqual(post.author, self.user)

    def test_new_post_user_off(self):
        """
        Проверка, что незарегистрированный пользователь
        редиректится на страницу входа
        """
        response = self.client_off.get(reverse('new_post'))
        reverse1 = reverse('login')
        reverse2 = reverse('new_post')
        self.assertRedirects(response,
            expected_url=f'{reverse1}?next={reverse2}',
            status_code=302,
            target_status_code=200,
            msg_prefix='',
            fetch_redirect_response=True
        )
        post = Post.objects.first()
        self.assertFalse(post)

    def test_view_new_post(self):
        """
        Проверка отображение нового поста
        """
        self._create_new_post()
        self.post = Post.objects.first()
        urls = self._get_url()
        for client in self.clients:
            for url in urls.values():
                response = self.client.get(url)
                self.assertContains(
                    response,
                    self.post.text,
                    count=None,
                    status_code=200,
                    msg_prefix='',
                    html=False)

    def _create_new_post(self):
        self.text_check = "test Text 1"
        self.client_on.post(
            reverse('new_post'),
            data={
                'text': self.text_check,
                'group': self.group1.id
            }
        )

    def _edit_post(self):
        self.text_check = "Измененный пост"
        self.response = self.client_on.post(
            reverse('post_edit',  kwargs={
                    'username': self.user.username, 'post_id': self.post.id}),
            data={'username': self.user.username,
                  'post_id': self.post.id,
                  })

    def test_edit_post_user_on(self):
        """
        Проверка редактирования поста
        зарегистрированным пользователем
        """
        self._create_new_post()
        self.post = Post.objects.select_related('author').first()
        self._edit_post()
        self.assertEqual(self.response.status_code,
            200, msg="Проверка редактирования поста"
        )
        self.post = Post.objects.select_related('author').first()
        urls = self._get_url()
        check_fields = (
            self.post.text, self.post.author.username)
        for test_url in urls.values():
            response = self.client.get(test_url)
            for check_field in check_fields:
                self.assertContains(
                    response,
                    check_field,
                    count=None,
                    status_code=200,
                    msg_prefix='',
                    html=False
                )

    def test_edit_post_view(self):
        """
        Проверка отображения отредактированного поста
        зарегистрированным пользователем
        """
        self._create_new_post()
        self.post = Post.objects.select_related('author', 'group').first()
        self._edit_post()
        self.post = Post.objects.select_related('group').first()
        check_fields = (self.post.text, self.post.author.username)
        urls = self._get_url()
        for test_url in urls.values():
            response = self.client.get(test_url)
            for check_field in check_fields:
                self.assertContains(
                    response,
                    check_field,
                    count=None,
                    status_code=200,
                    msg_prefix='',
                    html=False
                )

    def test_assert_contains(self):
        self._create_new_post()
        self.post = Post.objects.filter(author=self.user,
            text=self.text_check).first()
        urls = self._get_url()
        with open('posts/file.jpg', 'rb') as img:
            self.client_on.post(
                reverse('post_edit',  kwargs={
                        'username': self.user.username,
                        'post_id': self.post.id}
                ),
                {'author': self.user, 'text': 'post with image', 'image': img}
            )
            for test_url in urls.values():
                response = self.client.get(test_url)
                self.assertEqual(response.status_code,
                200, msg="Проверка редактирования поста")
                self.assertContains(
                        response,
                        '<img',
                        count=None,
                        status_code=200,
                        msg_prefix='',
                        html=False
                    )

    def test_img_view(self):
        self._create_new_post()
        self.post = Post.objects.filter(author=self.user,
                                        text=self.text_check).first()
        with tempfile.TemporaryDirectory() as temp_directory:
            with override_settings(MEDIA_ROOT=temp_directory):
                byte_image = io.BytesIO()
                im = Image.new("RGB", size=(500, 500), color=(255, 0, 0, 0))
                im.save(byte_image, format='jpeg')
                byte_image.seek(0)
                params = {'username': self.user.username,
                    'post_id': self.post.id}
                payload = {'text': 'post with image',
                    'image': ContentFile(byte_image.read(), name='test.jpeg')
                    }
                cache.clear()
                response = self.client_on.post(reverse('post_edit',
                    kwargs=params),
                    data=payload, follow=True
                    )
                self.assertEqual(response.status_code, 200)
                # Проверка на вхождение тега
                self.assertContains(response, '<img')

    def test_no_img_view(self):
        self._create_new_post()
        self.post = Post.objects.filter(author=self.user,
            text=self.text_check).first()
        with tempfile.TemporaryDirectory() as temp_directory:
            with override_settings(MEDIA_ROOT=temp_directory):
                byte_image = io.BytesIO()
                im = Image.new("RGB", size=(500, 500), color=(255, 0, 0, 0))
                im.save(byte_image, format='jpeg')
                byte_image.seek(0)
                params = {'username': self.user.username,
                    'post_id': self.post.id
                    }
                payload = {'text': 'post with image',
                    'image': ContentFile(byte_image.read(),
                    name='test.txt')
                    }
                cache.clear()
                response = self.client_on.post(reverse('post_edit',
                    kwargs=params),
                    data=payload, follow=True
                    )
                self.assertEqual(response.status_code, 200)

    def test_client_off_comment(self):
        """
        Только невторизованный пользователь не может комментировать посты
        """
        self._create_new_post()
        self.post = Post.objects.filter(author=self.user,
            text=self.text_check).first()
        cache.clear()
        response = self.client_off.post(reverse('add_comment',
            kwargs={'username': self.user.username, 'post_id': self.post.id})
            )
        reverse1 = reverse('login')
        reverse2 = reverse('add_comment',
            kwargs={'username': self.user.username,
            'post_id': self.post.id
            }
            )
        self.assertRedirects(response,
            expected_url=f'{reverse1}?next={reverse2}',
            status_code=302,
            target_status_code=200,
            msg_prefix='',
            fetch_redirect_response=True
        )

    def test_client_on_comment(self):
        self.text_check = "test Text Comment"
        response = self.client_on.post(
            reverse('new_post'),
            data={
                'text': self.text_check,
                'group': self.group1.id
            }
            )
        self.post = Post.objects.filter(author=self.user,
            text=self.text_check).first()
        response = self.client_on_2.post(reverse('add_comment',
            kwargs={'username': self.user.username, 'post_id': self.post.id}),
            data={'username': self.user_2,
                'post': self.post,
                'text': 'Комментарий авторизованного пользователя'}
                )
        self.assertRedirects(response,
            expected_url=reverse('post',
            kwargs={'username': self.user.username,
            'post_id': self.post.id}),
            status_code=302,
            target_status_code=200,
            msg_prefix='',
            fetch_redirect_response=True
            )
        post = Comment.objects.filter(author=self.user_2,
            post=self.post,
            text='Комментарий авторизованного пользователя').first()
        self.assertTrue(post)
        response = self.client_on_2.post(
            reverse('post',
                kwargs={'username': self.user.username,
                'post_id': self.post.id}))
        self.assertContains(
                    response,
                    'Комментарий авторизованного пользователя',
                    count=None,
                    status_code=200,
                    msg_prefix='',
                    html=False
                    )

    def test_follow(self):
        self.text_check = "test Text Follow"
        response = self.client_on.post(
            reverse('new_post'),
            data={
                'text': self.text_check,
                'group': self.group1.id
            }
        )
        response = self.client_on_2.post(reverse('profile_follow',
            kwargs={'username': self.user.username}),
            data={'username': self.user_2})
        follow = Follow.objects.filter(user=self.user_2, author=self.user)
        """ Пользователь может подписаться на другого пользователя """
        self.assertTrue(follow)
        response = self.client_on_2.post(reverse('follow_index'))
        """
        Пользователь может видеть записи пользователей,
        на которых подписался
        """
        self.assertContains(response,
            self.text_check,
            count=None,
            status_code=200,
            msg_prefix='',
            html=False)
        response = self.client_on_2.post(reverse('profile_unfollow',
            kwargs={'username': self.user.username}))
        follow = Follow.objects.filter(user=self.user_2, author=self.user)
        """ Пользователь может отписаться от другого пользователя """
        self.assertFalse(follow)
        response = self.client_on_2.post(reverse('follow_index'))
        """ Пользователь не видет записи пользователей,
        на которых не подписался """
        self.assertNotContains(response,
            self.text_check,
            status_code=200,
            msg_prefix='',
            html=False)
