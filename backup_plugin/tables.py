import logging
import django_tables2 as tables

from backup_plugin.models import Backup
from dcim.models import Device, Site
from netbox.tables import NetBoxTable, columns, ChoiceFieldColumn
from django.utils.translation import gettext as _

logger = logging.getLogger(f"netbox.plugins.{__name__}")


class BackupTable(NetBoxTable):
    name = tables.Column(linkify=True, verbose_name=_("Backup Diff"))

    orig_id = tables.Column()
    rev_id = tables.Column()

    device = tables.Column(
        verbose_name=_('Device'),
        orderable=True,
        linkify=True
    )

    manufacturer = tables.Column(
        verbose_name=_('Manufacturer'),
        accessor='device.device_type.manufacturer'
    )

    type = tables.Column(
        verbose_name=_('Device Type'),
        accessor='device.device_type'
    )

    region = tables.Column(
        verbose_name=_('Region'),
        accessor='device.site.region'
    )

    # created = tables.DateTimeColumn(format='m/d/Y')

    last_processed = tables.DateTimeColumn(format='m/d/Y')

    class Meta(NetBoxTable.Meta):
        model = Backup
        fields = (
            'pk', 'id', 'name', 'device', 'manufacturer', 'Device Type' 'region', 'orig_id', 'rev_id', 'last_processed'
        )
        default_columns = ('name', 'device', 'manufacturer', 'type', 'region', 'orig_id', 'rev_id', 'last_processed')

        # order last_processed descending so that the newest entries are first
        order_by = ('-last_processed', 'name')

