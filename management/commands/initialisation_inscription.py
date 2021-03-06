# -*- coding: utf-8 -*-
from django.conf import settings
from django_apogee.models import AnneeUni, VersionEtape as VersionEtapeApogee, EtpGererCge, Etape, ConfAnneeUni
from duck_inscription.models import SettingAnneeUni, SettingsEtape, Wish

__author__ = 'paul'
from django.core.management.base import BaseCommand
APOGEE_CONNECTION = getattr(settings, 'APOGEE_CONNECTION', 'oracle')


class Command(BaseCommand):
    def handle(self, *args, **options):
        #on récupére les personnes du jour (soit la date de création, de modif plus grand que la veille
        print u"debut d'initialisation"
        print u"création de settings pour les années universitaires"
        for annee in AnneeUni.objects.using('oracle').all():
            print annee
            annee.save(using='default')
            SettingAnneeUni.objects.get_or_create(cod_anu=annee.cod_anu, anneeuni_ptr=annee)
            ConfAnneeUni.objects.get_or_create(cod_anu=annee.cod_anu, anneeuni_ptr=annee)
        print u"création des étapes"
        s =SettingAnneeUni.objects.order_by('cod_anu').last()
        s.inscription=True
        s.save()
        for etape in Etape.objects.using('oracle').filter(etpgerercge__cod_cmp=settings.COMPOSANTE):
            etape.save(using='default')
            e = SettingsEtape.objects.get_or_create(cod_etp=etape.cod_etp, etape_ptr=etape)[0]

            e.label = etape.lib_etp
            e.save()
        print "fin initialisation"






