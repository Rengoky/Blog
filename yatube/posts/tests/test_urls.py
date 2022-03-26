from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='not_author')
        cls.author = User.objects.create_user(username='test_name1')
        cls.no_author = User.objects.create_user(username='no_author')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовая запись для создания нового поста',)

        cls.group = Group.objects.create(
            title='Заголовок для тестовой группы',
            slug='test_slug'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_home_url_exists_at_desired_location_guest(self):
        templates_url_names = {
            'posts:index.html': '/',
            'posts:group_list.html': f'/group/{self.group.slug}/',
            'posts/profile.html': f'/profile/{self.user}/',
            'posts/post_detail.html': f'/posts/{self.post.id}/',
        }
        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK, template)

    def test_create_list_url_exists_at_desired_location_authorized(self):
        templates_url_names = {
            'posts/create_post.html': '/create/',
            'posts/post_detail.html': f'/posts/{self.post.id}/edit/',
        }
        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK, template)

    def test_create_url_redirect_anonymous(self):
        """Страница /create/ перенаправляет анонимного пользователя."""
        response_guest = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response_guest, (reverse('users:login') + '?next=/create/')
        )

    def test_post_edit_list_url_redirect_anonymous(self):
        """Страница /posts/<post_id>/edit/ перенаправляет не автора."""
        response_guest = self.guest_client.get(f'/posts/{self.post.id}/edit/',
                                               follow=True)
        self.assertRedirects(
            response_guest,
            (reverse('users:login') + f'?next=/posts/{self.post.id}/edit/')
        )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'posts/index.html': '/',
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/',
            'posts/group_list.html': f'/group/{self.group.slug}/',
            'posts/create_post.html': '/create/',
            'posts/profile.html': f'/profile/{self.user}/',
            'posts/post_detail.html': f'/posts/{self.post.id}/',
        }
        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_page_404(self):
        response = self.guest_client.get('/qwerty228322/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
