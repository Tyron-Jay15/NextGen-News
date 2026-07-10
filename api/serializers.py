"""REST API serializers."""
from rest_framework import serializers

from accounts.models import User
from authors.models import AuthorProfile
from categories.models import Category, Tag
from comments.models import Comment
from news.models import Article


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'icon', 'image', 'parent', 'is_active']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'is_trending', 'usage_count']


class AuthorSerializer(serializers.ModelSerializer):
    article_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = AuthorProfile
        fields = ['id', 'display_name', 'slug', 'biography', 'photo', 'job_title', 'article_count']


class ArticleListSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.display_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'subtitle', 'slug', 'excerpt', 'hero_image', 'video_url', 'author_name',
            'category_name', 'status', 'is_featured', 'is_breaking', 'view_count',
            'reading_time_minutes', 'published_at',
        ]


class ArticleDetailSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Article
        fields = '__all__'
        read_only_fields = ['view_count', 'share_count', 'comment_count', 'created_by']


class ArticleWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = [
            'title', 'subtitle', 'excerpt', 'body', 'hero_image', 'video_url', 'author', 'category',
            'tags', 'status', 'article_type', 'province', 'municipality',
            'is_featured', 'is_breaking', 'seo_title', 'seo_description', 'scheduled_at',
        ]


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'article', 'body', 'author_name', 'status', 'likes', 'dislikes', 'created_at']
        read_only_fields = ['status', 'likes', 'dislikes']

    def get_author_name(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.email
        return obj.author_name


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'role', 'avatar']
        read_only_fields = ['email']
