# coding=utf-8
from __future__ import unicode_literals

from crispy_forms.bootstrap import TabHolder, Tab
from django.core.urlresolvers import reverse
from django.forms.models import inlineformset_factory
from xadmin.views import filter_hook, CommAdminView
from duck_theme_ied.xadmin_plugins.topnav import IEDPlugin
from xadmin.plugins.auth import UserAdmin
from xadmin.layout import Main, Fieldset, Side
import xadmin
from duck_inscription.models import Individu, SettingsEtape, WishWorkflow, SettingAnneeUni, ListeDiplomeAces
from duck_inscription.models import Wish, SuiviDossierWorkflow, IndividuWorkflow, SettingsUser, CursusEtape
from xadmin.util import User
from duck_inscription.adminx.html_string.action_adminx import ACTION, DOSSIER_INCOMPLET
from duck_inscription.models.piece_dossier_models import CategoriePieceModel, PieceDossierModel


class WishInline(object):
    def email(self, obj):
        return obj.individu.personal_email

    def reins(self, obj):
        if obj.is_reins:
            return 'oui'
        else:
            return 'non'

    def label(self, obj):
        return "{} {}".format(obj.code_dossier, obj.etape.label)

    def info_paiement(self, obj):
        """
        Pour l'admin
        :return:
        """
        response = ""
        try:
            response += "type de paiement : {} <br>".format(obj.paiementallmodel.moyen_paiement)
            if obj.paiementallmodel.moyen_paiement.type == 'CB':
                response += "transaction : {} <br> numéro de commande : {}<br>".format(obj.paiementallmodel.paiement_request.vads_trans_id, obj.paiementallmodel.pk)
                r = ''
                for p in obj.paiementallmodel.paiement_request.status_paiement()['transactionItem']:
                    r += 'date : {date}, montant : {montant} , status: {status} <br>'.format(date=p['expectedCaptureDate'],
                                                                                        montant=str(p['amount'])[:-2]+','+str(p['amount'])[-2:],
                                                                                        status=p['transactionStatusLabel'])
                    if p['transactionStatusLabel'] == 'CAPTURED':
                        r += '<span class="label label-success">Ok</span><br>'
                    else:
                        r += '<span class="label label-danger">Annomalie</span><br>'
                response += '<br>' + r
        except Exception as e:
            pass
        return response
    info_paiement.allow_tags = True
    info_paiement.short_description = 'info paiment'

    def actions(self, obj):
        result = ' '
        if obj.state.is_inscription or obj.state.is_dispatch:
            url = reverse('changement_centre', kwargs={'pk': obj.pk})
            result += ACTION.format(id=obj.pk, url=url)
        if obj.state.is_inscription:
            url =  reverse('dossier_incomplet', kwargs={'pk': obj.pk})
            result += DOSSIER_INCOMPLET.format(id=obj.pk, url=url)

        return result

    actions.allow_tags = True
    actions.short_description = 'action'

    def description(self, obj):
        test = """
        <table>
            <tr>
                <td>centre gestion :</td>
                <td>{}</td>
            <tr>
            <tr><td>reinscription :</td><td>{}</td></tr>
            <tr>
                <td>date liste inscription :</td>
                <td>{}</td>
            </tr>
        </table>
        """
        centre_gestion = obj.centre_gestion or ''
        reins = self.reins(obj)
        date_liste_inscription = obj.date_liste_inscription or ''
        return test.format(centre_gestion, reins, date_liste_inscription)

    description.allow_tags = True
    reins.short_description = 'Réinscription'

    model = Wish
    extra = 0
    style = 'table'
    fields = ['email', 'annee']
    readonly_fields = [
                       'get_transition_log',
                       'info_paiement', 'get_suivi_dossier', 'print_dossier_equi', 'actions', 'help_superuser']
    exclude = ['annee','demi_annee', 'is_reins', 'is_auditeur', 'diplome_acces', 'centre_gestion', 'reins', 'date_validation',
               'valide', 'date_liste_inscription', 'suivi_dossier', 'code_dossier']
    can_delete = True
    hidden_menu = True

    def queryset(self):
        queryset = super(WishInline, self).queryset()
        return queryset.filter(annee__inscription=True)

    def help_superuser(self, obj):
        reponse = ''
        reponse += 'code_dossier : {} <br>'.format(obj.code_dossier)
        reponse += 'valide : {} <br>'.format(obj.valide)
        reponse += 'is_reins : {} <br>'.format(obj.is_reins)
        reponse += 'diplome acces : {} <br>'.format(obj.diplome_acces)
        reponse += 'centre gestion : {} <br>'.format(obj.centre_gestion)
        reponse += 'date validation : {} <br>'.format(obj.date_validation)
        reponse += 'date liste attente inscription : {} <br>'.format(obj.date_liste_inscription)
        reponse += 'centre gestion : {} <br>'.format(obj.centre_gestion)
        return reponse
    help_superuser.allow_tags = True

    @filter_hook
    def get_readonly_fields(self):
        if self.request.user.is_superuser:
            return self.readonly_fields
        else:
            return ['label', 'description', 'info_paiement',  'current_state', 'get_transition_log', 'get_suivi_dossier',
                    'print_dossier_equi', 'actions']

    @property
    def get_exclude(self):
        if self.request.user.is_superuser:
            return self.exclude
        else:
            return self.exclude + ['valide', 'diplome_acces', 'date_validation', 'etape', 'demi_annee', 'is_ok',
                                   'centre_gestion', 'date_liste_inscription', 'suivi_dossier', 'state', 'is_auditeur']

    @filter_hook
    def get_formset(self, **kwargs):
        """Returns a BaseInlineFormSet class for use in admin add/change views."""
        if self.get_exclude is None:
            exclude = []
        else:
            exclude = list(self.get_exclude)
        exclude.extend(self.get_readonly_fields())
        if self.get_exclude is None and hasattr(self.form, '_meta') and self.form._meta.exclude:
            # Take the custom ModelForm's Meta.exclude into account only if the
            # InlineModelAdmin doesn't define its own.
            exclude.extend(self.form._meta.exclude)
        # if exclude is an empty list we use None, since that's the actual
        # default
        exclude = exclude or None
        can_delete = self.can_delete and self.has_delete_permission()
        defaults = {"form": self.form, "formset": self.formset, "fk_name": self.fk_name, "exclude": exclude,
                    "formfield_callback": self.formfield_for_dbfield, "extra": self.extra, "max_num": self.max_num,
                    "can_delete": can_delete, }
        defaults.update(kwargs)
        return inlineformset_factory(self.parent_model, self.model, **defaults)

    def get_transition_log(self, obj):
        reponse = '<table>'
        for transition in obj.parcours_dossier.all():
            reponse += '<tr><td>{}</td><td>{}</td></tr>'.format(WishWorkflow.states[transition.to_state].title,
                                                                transition.timestamp.strftime('%d/%m/%Y %H:%M:%S'))
        reponse += '</table>'
        return reponse

    get_transition_log.short_description = 'parcours'
    get_transition_log.allow_tags = True

    def get_suivi_dossier(self, obj):
        reponse = '<table>'
        for transition in obj.etape_dossier.all():
            reponse += '<tr><td>{}</td><td>{}</td></tr>'.format(SuiviDossierWorkflow.states[transition.to_state].title,
                                                                transition.timestamp.strftime('%d/%m/%Y %H:%M:%S'))
        reponse += '</table>'
        return reponse

    get_suivi_dossier.short_description = 'suivi'
    get_suivi_dossier.allow_tags = True

    def current_state(self, obj):
        return WishWorkflow.states[obj.state].title

    current_state.short_description = 'Etat du dossier'
    current_state.allow_tags = True

    def print_dossier_equi(self, obj):
        url = reverse('impression_equivalence', kwargs={'pk': obj.pk})
        url2 = reverse('impression_decision_equivalence', kwargs={'pk': obj.pk})
        url_inscription = reverse('inscription_pdf', kwargs={'pk': obj.pk})
        url_candidature = reverse('candidature_pdf', kwargs={'pk': obj.pk})
        url_courrier_pieces_manquantes = reverse('pieces_manquantes_pdf', kwargs={'pk': obj.pk})

        reponse = ' '

        if obj.etape.date_ouverture_equivalence and not obj.is_reins:
            reponse += '<a href="{}" class="btn btn-primary">Dossier Equivalence</a>'.format(url)
            if obj.etape.grille_de_equivalence:
                reponse += '<a href="{}" class="btn btn-primary">Decision Equivalence</a>'.format(url2)
            reponse += '<hr>'
        if obj.etape.date_ouverture_candidature and not obj.is_reins:
            reponse += '<a href="{}" class="btn btn-primary">Dossier Candidature</a><hr>'.format(url_candidature)
        if obj.state in ['inscription', 'liste_attente_inscription']:
            reponse += '<a href="{}" class="btn btn-primary">Dossier inscription</a>'.format(url_inscription)
        if hasattr(obj, 'dossier_pieces_manquantes') and obj.dossier_pieces_manquantes.pieces.count() and obj.state.is_inscription:
            reponse += '<hr>'
            reponse += '<a href="{}" class="btn btn-primary">Courrier pièces manquantes</a>'.format(url_courrier_pieces_manquantes)


        return reponse

    print_dossier_equi.allow_tags = True
    print_dossier_equi.short_description = 'Impression'


class IndividuXadmin(object):
    site_title = 'Consultation des dossiers étudiants'
    show_bookmarks = False
    fields = ('code_opi', 'last_name', 'first_name1', 'birthday', 'personal_email', 'state', 'user', 'get_url')
    readonly_fields = (
        'user', 'student_code', 'code_opi', 'last_name', 'first_name1', 'birthday', 'personal_email',
        'numeros_telephones', 'get_transition_log', 'get_url')
    list_display = ('__unicode__', 'last_name')
    list_per_page = 10
    search_fields = ('last_name', 'first_name1', 'common_name', 'student_code', 'code_opi', 'wishes__code_dossier')
    list_exclude = ('id', 'personal_email_save', 'opi_save', 'year')
    list_select_related = None
    inlines = [WishInline]
    hidden_menu = True

    def get_url(self, obj):
        response = '<a href="{}" target="_blank">{}</a>'
        return response.format(obj.get_absolute_url(), obj.get_absolute_url())
    get_url.short_description = 'voir sur le site'
    get_url.allow_tags = True

    def has_add_permission(self):
        return False

    def has_delete_permission(self, obj=None):
        return False

    @filter_hook
    def get_readonly_fields(self):
        if self.request.user.is_superuser:
            return self.readonly_fields
        else:
            return self.readonly_fields + ('state', )

    def get_transition_log(self, obj):
        reponse = '<table>'
        for transition in obj.etape_dossier.all():
            reponse += '<tr><td>{}</td><td>{}</td></tr>'.format(IndividuWorkflow.states[transition.to_state],
                                                                transition.timestamp.strftime('%d/%m/%Y %H:%M:%S'))
        reponse += '</table>'
        return reponse

    get_transition_log.short_description = 'parcours'
    get_transition_log.allow_tags = True


class ListeDiplomeAcesInline(object):
    model = ListeDiplomeAces
    extra = 1


class SettingsEtapeXadmin(object):
    exclude = ('lib_etp', 'cod_cyc', 'cod_cur', 'annee')
    list_display = ['__unicode__', 'date_ouverture_inscription', 'date_fermeture_inscription',
                    'date_fermeture_reinscription', 'droit', 'frais']
    list_filter = ['cursus']
    quickfilter = ['cursus']
    inlines = [ListeDiplomeAcesInline]

    form_layout = (
        Main(Fieldset('Etape', 'cod_etp', 'diplome', 'cursus', 'label', 'label_formation'), TabHolder(Tab('Equivalence',
                                                                                                          Fieldset('',
                                                                                                                   'date_ouverture_equivalence',
                                                                                                                   'date_fermeture_equivalence',
                                                                                                                   'document_equivalence',
                                                                                                                   'path_template_equivalence',
                                                                                                                   'grille_de_equivalence')),
                                                                                                      Tab('Candidature',
                                                                                                          Fieldset('',
                                                                                                                   'date_ouverture_candidature',
                                                                                                                   'date_fermeture_candidature',
                                                                                                                   'note_maste',
                                                                                                                   'document_candidature', )),
                                                                                                      Tab('Inscription',
                                                                                                          Fieldset('',
                                                                                                                   'date_ouverture_inscription',
                                                                                                                   'date_fermeture_inscription',
                                                                                                                   'date_fermeture_reinscription',
                                                                                                                   'autres',
                                                                                                                   'droit',
                                                                                                                   'frais',
                                                                                                                   'nb_paiement',
                                                                                                                   'demi_tarif',
                                                                                                                   'semestre',
                                                                                                                   'limite_etu'
                                                                                                                   ))
                                                                                                      )),
        Side(Fieldset('Settings', 'required_equivalence', 'is_inscription_ouverte'))
    )
    def get_readonly_fields(self):
        if self.user.is_superuser:
            return []
        return ['diplome', 'cursus', 'label', 'label_formation', 'cod_etp']


class UserSettingsInline(object):
    model = SettingsUser
    style_fields = {'etapes': 'm2m_transfer'}
    can_delete = False
    extra = 1
    max_num = 1


class CustomUserAdmin(UserAdmin):
    inlines = [UserSettingsInline]


class OpiView(object):
    model = Wish
    show_bookmarks = False
    list_export = []
    list_per_page = 10
    search_fields = ['code_dossier', 'individu__last_name', 'individu__first_name1']
    hidden_menu = True
    list_display = ('__str__', 'info_manquante', 'opi_url')

    def opi_url(self, obj):
        url = reverse('remontee_opi')
        if obj.state.is_inscription:
            if obj.paiementallmodel.moyen_paiement.type == 'CB':
                valide = True
                for p in obj.paiementallmodel.paiement_request.status_paiement()['transactionItem']:
                    valide = valide and (p['transactionStatusLabel'] in ['CAPTURED', 'WAITING_AUTHORISATION'])
                if not valide:
                    return '<br><span class="label label-danger">Annomalie</span><a class="btn btn-primary" href="{}?opi={}">Remontée Opi</a>'.format(url, obj.code_dossier)
            return '<br><span class="label label-success">Ok</span><a class="btn btn-primary" href="{}?opi={}">Remontée Opi</a>'.format(url, obj.code_dossier)
        else:
            return ''

    def info_manquante(self, obj):
        dossier_inscription = obj.individu.dossier_inscription
        reponse = ""
        reponse += "annee dernier diplome" + unicode(dossier_inscription.annee_dernier_diplome) + "<br>"
        return reponse

    info_manquante.allow_tags = True
    info_manquante.short_description = 'info manquante'

    opi_url.short_description = 'remontee opi'
    opi_url.allow_tags = True
    opi_url.is_column = True

    def has_delete_permission(self, obj=None):
        return False

    def has_add_permission(self):
        return False


xadmin.site.unregister(User)
xadmin.site.register(User, CustomUserAdmin)
xadmin.site.register(Individu, IndividuXadmin)
xadmin.site.register(SettingsEtape, SettingsEtapeXadmin)
xadmin.site.register_plugin(IEDPlugin, CommAdminView)
xadmin.site.register(CursusEtape)
xadmin.site.register(SettingAnneeUni)
xadmin.site.register(Wish, OpiView)
xadmin.site.register(CategoriePieceModel)
xadmin.site.register(PieceDossierModel)