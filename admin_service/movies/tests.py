from django.test import TestCase

from .models import Filmwork


class FilworkTestCase(TestCase):
    def setUp(self):
        Filmwork.objects.create()
