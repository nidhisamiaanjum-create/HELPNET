from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class VerificationPrivateStorage(FileSystemStorage):
    """Private disk storage; documents are served only by admin-only views."""

    def __init__(self):
        super().__init__(location=settings.PRIVATE_MEDIA_ROOT)

    def url(self, name):
        raise ValueError("Verification documents require an authorized download endpoint.")
