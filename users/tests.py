from django.test import TestCase
from django.test import Client
from posts.models import User
from django.urls import reverse


class TestProlil(TestCase):
    def setUp(self):
        self.client = Client()
        self.client_off = Client()
        self.user = User.objects.create(
            username='test_user', email='q@q.com')
        self.user.set_password('123')
        self.user.save()
        self.client.force_login(self.user)
        self.clients = (self.client, self.client_off,)

    def test_profile(self):
        for client in self.clients:
            response = self.client.get(
                reverse('profile', kwargs={'username': self.user.username})
            )
            self.assertEqual(
                response.status_code, 200,
                msg="Проверка, что страница profile пользователя ")
