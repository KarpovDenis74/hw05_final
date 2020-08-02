from django.test import TestCase
from django.test import Client
from posts.models import User



class TestYatube(TestCase):
    def setUp(self):
        self.client_on = Client()
        self.client_off = Client()
        self.user = User.objects.create(
            username='test_user', email='q@q.com')
        self.user.set_password('123')
        self.user.save()
        self.client_on.force_login(self.user)
        self.clients = (self.client_on, self.client_off,)

    def test_404(self):
        """
        Проверка, что при неправильном адресе происходит
        перенаправление на страницу 404
        """
        for client in self.clients:
            response = self.client.get('fdgdfgdfg')
            self.assertEqual(response.status_code, 404)
