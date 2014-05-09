# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django_xworkflows.xworkflow_log.models import TransitionLog
from django_apogee.models import AnneeUni, VersionEtape as VersionEtapeApogee, EtpGererCge, Etape
from duck_inscription.models import SettingAnneeUni, SettingsEtape, Wish

__author__ = 'paul'
from django.core.management.base import BaseCommand
APOGEE_CONNECTION = getattr(settings, 'APOGEE_CONNECTION', 'oracle')


class Command(BaseCommand):
    def handle(self, *args, **options):
        # on récupére les personnes du jour (soit la date de création, de modif plus grand que la veille
        t = ContentType.objects.get(model='wish')
        pks = [t.content_id for t in TransitionLog.objects.filter(content_type=t, transition='equivalence_reception')]
        wishes = Wish.objects.filter(pk__in=pks, etape__cod_etp__in=['L1NPSY', 'L2NPSY', 'L3NPSY'])





