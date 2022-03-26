from django.test import TestCase

from posts.models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='текст'
        )

    def test_models_have_correct_object_names(self):
        group = PostModelTest.group
        post = PostModelTest.post
        self.assertEqual(str(group), group.title)
        self.assertEqual(str(post), post.text[:15])

    def test_group_verbose_name(self):
        group = PostModelTest.group

        group_field_verboses = {
            'title': 'Заголовок группы',
            'slug': 'Слаг',
            'description': 'Описание',
        }

        for field_key, expected_value in group_field_verboses.items():
            with self.subTest(field_key=field_key):
                self.assertEqual(
                    group._meta.get_field(field_key).verbose_name,
                    expected_value)

    def test_post_verbose_name(self):
        post = PostModelTest.post

        post_field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }

        for field_key, expect_value in post_field_verboses.items():
            with self.subTest(field_key=field_key):
                self.assertEqual(
                    post._meta.get_field(field_key).verbose_name, expect_value)

    def test_group_help_text(self):
        group = PostModelTest.group

        group_field_help_texts = {
            'title': 'Добавьте название группы',
            'slug': 'Добавьте слаг',
            'description': 'Добавьте описание',
        }

        for field_key, expected_value in group_field_help_texts.items():
            with self.subTest(field_key=field_key):
                self.assertEqual(
                    group._meta.get_field(field_key).help_text, expected_value)

    def test_post_help_text(self):
        post = PostModelTest.post

        post_field_help_texts = {
            'text': 'Введите текст поста',
            'pub_date': 'Добавьте дату публикации',
            'author': 'Впишите имя автора поста',
            'group': 'Выберите группу',
        }

        for field_key, expected_value in post_field_help_texts.items():
            with self.subTest(field_key=field_key):
                self.assertEqual(
                    post._meta.get_field(field_key).help_text, expected_value)
