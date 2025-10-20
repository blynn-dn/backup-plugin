import json
import logging
from functools import cached_property

from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from dcim.models import Device, Site
from netbox.models import NetBoxModel

logger = logging.getLogger(f"netbox.backup_plugin.{__name__}")


class Backup(NetBoxModel):
    name = models.CharField(max_length=100)
    device = models.ForeignKey(
        to='dcim.Device', on_delete=models.PROTECT,
        related_name='+',
        blank=True,
        null=True
    )
    orig_id = models.PositiveIntegerField()
    rev_id = models.PositiveIntegerField()
    diff_info = models.JSONField(blank=True, null=True, verbose_name="Diff Info", default=list)
    diff = models.TextField(blank=True)
    last_processed = models.DateTimeField(blank=True, null=True)

    @property
    def process_date(self):
        return self.created.date()

    # @property
    # def diff_info_data(self):
    #     return json.loads(self.diff_info)

    @cached_property
    def attributes(self):
        logger.info(f"device: {self.device}, {type(self.device)}")
        info = []
        if not self.device:
            return ''

        if self.device.tags.names():
            info.append("Tags: " + ", ".join([t.name for t in self.device.tags.all()]))
        info.append(f"Status: {getattr(self.device, 'status', None)}")

        if self.device.custom_field_data.get('poller'):
            info.append(f"Poller: {self.device.custom_field_data.get('poller')}")
        if self.device.primary_ip4:
            info.append(f"Primary IP4: {str(self.device.primary_ip4)}")
        info.append(f"Region: {self.device.site.region.name}")

        if self.device.serial:
            info.append(f"Serial: {self.device.serial}")
        info.append(f"Device Type: {getattr(self.device.device_type, 'model', None)}")

        if self.device.platform:
            info.append(f"Platform: {getattr(self.device.platform, 'name', None)}")
        elif isinstance(self.device, Site):
            info.append(f"Region:  {self.device.region.name}")
        return ''.join(
            [f'<span class="badge text-bg-secondary text-dark" style="user-select:all;"> {i} </span> ' for i in info])

    class Meta:
        ordering = ['last_processed']

    def get_absolute_url(self):
        return reverse('plugins:backup_plugin:backup', args=[self.pk])

    def __str__(self):
        return self.name
