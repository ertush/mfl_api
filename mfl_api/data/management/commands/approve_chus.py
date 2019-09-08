
from django.core.management import BaseCommand

from chul.models import CommunityHealthUnit


def approve_chus(chu):
    chu.is_approved = True
    chu.save()


class Command(BaseCommand):

    def handle(self, *args, **options):
        def approve_community_units():
            for chu in CommunityHealthUnit.objects.all():
                approve_chus(chu)

        approve_community_units()
