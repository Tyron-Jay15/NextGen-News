"""Media library storage."""
from django.core.files.storage import FileSystemStorage


class MediaStorage(FileSystemStorage):
    location = 'media/ckeditor'
    base_url = '/media/ckeditor/'
