from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class HealthCredentialStorage(FileSystemStorage):
    """Keep submitted health credentials outside publicly served media."""

    def __init__(self):
        super().__init__(location=settings.PRIVATE_MEDIA_ROOT)

    def url(self, name):
        raise ValueError("Health credentials require an authorized download endpoint.")
