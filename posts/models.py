from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        verbose_name="Название сообщества",
        max_length=200)
    slug = models.SlugField(verbose_name="Slug сообщества", unique=True)
    description = models.TextField(verbose_name="Описание сообщества")

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        verbose_name="Текст поста",
        )
    pub_date = models.DateTimeField("date published",
                                    auto_now_add=True,
                                    db_index=True
                                    )
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name="posts")
    group = models.ForeignKey(Group,
                              on_delete=models.SET_NULL,
                              related_name="post_group",
                              blank=True,
                              null=True)
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    def __str__(self):
        return self.text

    class Meta:
        ordering = ['-pub_date']


class Comment(models.Model):
    post = models.ForeignKey(Post,
                            on_delete=models.CASCADE,
                            related_name="comments"
                            )
    author = models.ForeignKey(User,
                            on_delete=models.CASCADE,
                            related_name="comments"
                            )
    text = models.TextField(
        verbose_name="Текст комментария",
    )
    created = models.DateTimeField("date created",
                            auto_now_add=True,
                            db_index=True
                            )

    def __str__(self):
        return self.text

    class Meta:
        ordering = ['-created']


class Follow(models.Model):
    user = models.ForeignKey(User,
                            on_delete=models.CASCADE,
                            related_name="follower"
                            )
    author = models.ForeignKey(User,
                            on_delete=models.CASCADE,
                            related_name="following"
                            )
