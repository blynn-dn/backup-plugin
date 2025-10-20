import logging

from dcim.models import Device, DeviceType, Region
from netbox.forms import NetBoxModelForm, NetBoxModelFilterSetForm
from utilities.forms.fields import CommentField, DynamicModelMultipleChoiceField

from utilities.forms.widgets import DateTimePicker
from .models import  Backup
from django import forms
from django.utils.translation import gettext as _


logger = logging.getLogger(f"netbox.plugins.{__name__}")


class BackupForm(NetBoxModelForm):
    comments = CommentField()
    # diff = CommentField(label=_('Diff'))
    orig_id = forms.IntegerField()
    diff = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = Backup
        fields = ('name', 'device', 'orig_id', 'rev_id', 'diff', 'comments')


def get_backup_process_date_choices():
    """
    Returns a list of distinct created date choices by ordering Backup records by created date. The idea is to
    create a distinct list of dates for each daily backup.

    Returns:
        list(tuple): List of Choices (label and value)
    """
    return [(o.last_processed.date(), o.last_processed.date()) for o in Backup.objects.all().order_by(
        'last_processed__date').distinct('last_processed__date')]


class BackupFilterForm(NetBoxModelFilterSetForm):
    model = Backup

    device = forms.ModelMultipleChoiceField(
        queryset=Device.objects.all(),
        required=False
    )

    # this will render a list of the available daily backup days
    last_processed = forms.ChoiceField(choices=get_backup_process_date_choices)

    device_type = DynamicModelMultipleChoiceField(
        queryset=DeviceType.objects.all(),
        required=False,
        label=_('Device type')
    )

    region = DynamicModelMultipleChoiceField(
        queryset=Region.objects.all(),
        required=False,
        label=_('Region')
    )
