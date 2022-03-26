import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    post_text = 'Тестовый текст'
    post_author = 'auth'
    post_group = 'Тестовая группа'
    group_description = 'Тестовое описание'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.post_user = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=uploaded
        )
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        templates_pages_names = {
            'posts/create_post.html': reverse('posts:post_create'),
            'posts/post_detail.html':
                reverse('posts:post_detail',
                        kwargs={'post_id': str(self.post_user.pk)}),
            'posts/profile.html':
                reverse('posts:profile', kwargs={'username': 'auth'}),
            'posts/group_list.html':
                reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            'posts/index.html': reverse('posts:index'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_edit_page_uses_correct_template(self):
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': str(self.post_user.pk)}))
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_home_page_show_correct_context(self):
        response = self.guest_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        post_group_0 = first_object.group.title
        post_image_0 = Post.objects.exists()
        self.assertEqual(post_text_0, self.post_text)
        self.assertEqual(post_author_0, self.post_author)
        self.assertEqual(post_group_0, self.post_group)
        self.assertTrue(post_image_0, 'posts/small.gif')

    def test_posts_group_list_correct_context(self):
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}))
        post_image_0 = Post.objects.exists()
        self.assertEqual(response.context.get('group').title,
                         self.post_group)
        self.assertEqual(response.context.get('group').description,
                         self.group_description)
        self.assertTrue(post_image_0, 'posts/small.gif')

    def test_profile_correct_context(self):
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': 'auth'}))
        post_image_0 = Post.objects.exists()
        self.assertEqual(response.context.get('author').username,
                         self.post_author)
        self.assertTrue(post_image_0, 'posts/small.gif')

    def test_post_detail_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post_user.pk}))
        post_image_0 = Post.objects.exists()
        self.assertEqual(response.context.get('post').text, self.post_text)
        self.assertTrue(post_image_0, 'posts/small.gif')

    def test_create_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_create'))
        self.assertIsInstance(response.context.get('form'), PostForm)

    def test_edit_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post_user.pk}))
        self.assertIsInstance(response.context.get('form'), PostForm)
        self.assertTrue(response.context['is_edit'])


class PaginatorViewsTest(TestCase):
    TEN_POSTS = 10
    THREE_POSTS = 3

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        for i in range(13):
            Post.objects.create(
                author=cls.user,
                text='Тестовый текст' + str(i),
                group=cls.group,
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_home_page_contains_ten_records(self):
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), self.TEN_POSTS)

    def test_second_home_page_contains_three_records(self):
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), self.THREE_POSTS)

    def test_first_group_list_page_contains_ten_records(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}))
        self.assertEqual(len(response.context['page_obj']), self.TEN_POSTS)

    def test_second_group_list_page_contains_three_records(self):
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': 'test-slug'}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), self.THREE_POSTS)

    def test_first_profile_page_contains_ten_records(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'auth'}))
        self.assertEqual(len(response.context['page_obj']), self.TEN_POSTS)

    def test_second_profile_page_contains_ten_records(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'auth'}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), self.THREE_POSTS)


class PostIntegrationViewsTests(TestCase):
    post_text = 'Тестовый текст'
    post_group_1 = 'Тестовая группа 1'
    post_group_2 = 'Тестовая группа 2'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа 1',
            slug='test-slug-1',
            description='Тестовое описание 1',
        )
        cls.group_second = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание 2',
        )
        cls.post_user = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_group_test_of_created_post(self):
        response_index = self.authorized_client.get(reverse('posts:index'))
        response_group = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': 'test-slug-1'}))
        response_profile = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': 'auth'}))
        self.assertEqual(response_index.context['page_obj'][0].text,
                         self.post_text)
        self.assertEqual(response_index.context['page_obj'][0].group.title,
                         self.post_group_1)
        self.assertIsNot(response_index.context['page_obj'][0].group.title,
                         self.post_group_2)
        self.assertEqual(response_group.context['page_obj'][0].text,
                         self.post_text)
        self.assertEqual(response_profile.context['page_obj'][0].text,
                         self.post_text)


class CacheTests(TestCase):
    post_text = "Тестовый текст"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")

        cls.post_user = Post.objects.create(
            author=cls.user,
            text="Тестовый текст",
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_of_home_page(self):
        post_exits = (self.guest_client.get(reverse
                                            ("posts:index"))
                      .content)
        self.post_user.delete()
        post_deleted = (self.guest_client.get(reverse
                                              ("posts:index"))
                        .content)
        self.assertEqual(post_exits, post_deleted)
        cache.clear()
        cache_cleared = (self.guest_client.get(reverse
                                               ("posts:index"))
                         .content)
        self.assertNotEqual(post_exits, cache_cleared)


class FollowTests(TestCase):
    def setUp(self):
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.user_follower = User.objects.create_user(username='follower')
        self.user_following = User.objects.create_user(username='following')
        self.post = Post.objects.create(
            author=self.user_following,
            text='Тестовая запись для тестирования ленты'
        )
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)

    def test_follow(self):
        self.client_auth_follower.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user_following.username}))
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        self.client_auth_follower.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user_following.username}))
        self.client_auth_follower.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.user_following.username}))
        self.assertEqual(Follow.objects.all().count(), 0)
