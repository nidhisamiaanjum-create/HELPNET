from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class VolunteerPrivateCertificateStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(location=settings.PRIVATE_MEDIA_ROOT, base_url="/private-certificates/")

    def url(self, name):
        raise ValueError("Private certificates must be accessed through the authorized download endpoint.")