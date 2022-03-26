from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Post, User


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='lev')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_new_post_created_in_database(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст',
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post = Post.objects.first()
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(post.text, 'Текст')
        self.assertEqual(post.author.username, 'lev')
        self.assertEqual(post.group, None)

    def test_new_post_not_created_in_database(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст'
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('users:login')
                             + '?next='
                             + reverse('posts:post_create'))

        self.assertEqual(Post.objects.count(), posts_count)

    def test_post_edited_in_database(self):
        post_id = self.post.pk
        form_data_edited = {
            'text': 'Отредактированный текст',
        }
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post_id}),
            data=form_data_edited,
            follow=True
        )
        post = Post.objects.get(id=self.post.id)
        self.assertTrue(Post.objects.filter(
            text=form_data_edited.get('text')).exists())
        self.assertEqual(post.text, 'Отредактированный текст')
        self.assertEqual(post.author.username, 'lev')

    def test_create_comment(self):
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Коммент',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        comment = Comment.objects.first()
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(Comment.objects.count(), comments_count + 1)
