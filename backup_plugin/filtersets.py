import logging

from django.db.models import Q, Max
from django.utils.translation import gettext as _
import django_filters

from dcim.models import Device, DeviceType, Region
from netbox.filtersets import NetBoxModelFilterSet
from utilities.forms.fields import ColorField, DynamicModelMultipleChoiceField, TagFilterField

from utilities.filters import MultiValueCharFilter
from .models import Backup

logger = logging.getLogger(f"netbox.plugins.{__name__}")


class BackupFilterSet(NetBoxModelFilterSet):
    device_id = django_filters.ModelMultipleChoiceFilter(
        field_name="device__name",
        queryset=Device.objects.all(),
        to_field_name="id",
        label=_("Device"),
    )

    device_type = django_filters.ModelMultipleChoiceFilter(
        field_name="device__device_type__id",
        queryset=DeviceType.objects.all(),
        to_field_name="id",
        required=False,
        label=_('Device type')
    )

    region = django_filters.ModelMultipleChoiceFilter(
        field_name="device__site__region__id",
        queryset=Region.objects.all(),
        to_field_name="id",
        label=_('Region')
    )

    # This will generate a filterset for matching the daily backup days. ex: process_date=2025-07-02
    # Which is exactly what a query like this would generate `Backup.objects.filter(created__date='2025-07-02')`
    process_date = django_filters.DateFilter(field_name='created__date', lookup_expr='exact')

    last_processed = django_filters.DateFilter(field_name='last_processed__date', lookup_expr='exact', required=False)

    # process_date = django_filters.ChoiceFilter(choices=get_backup_process_date_choices)
    # Backup.objects.all().order_by('created__date').distinct('created__date').first().created.date()

    # @property
    # def qs(self):
    #     parent = super().qs
    #     if 'process_date' not in self.request.GET.dict():
    #         # if process_date not set then default to the most recent processing date (day)
    #         return parent.filter(
    #             created__date=Backup.objects.aggregate(max_date=Max('created__date'))['max_date']
    #         )
    #
    #     return parent

    class Meta:
        model = Backup
        fields = ('id', 'name', 'device', 'last_processed')

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) | Q(device__name__icontains=value) |
            Q(device__device_type__manufacturer__name__icontains=value) |
            Q(device__device_type__model__icontains=value) |
            Q(device__site__region__name__icontains=value) |
            Q(diff__icontains=value)
        )

