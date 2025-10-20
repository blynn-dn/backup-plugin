import logging

from django.db.models import Max

from . import forms, models, tables, filtersets
from netbox.views.generic import ObjectEditView, ObjectListView, ObjectView, ObjectDeleteView

from utilities.views import ContentTypePermissionRequiredMixin, ViewTab, register_model_view
from netbox.views import generic
from dcim.models import Device

from backup_plugin.utils.unimus import config, Client

logger = logging.getLogger(f"netbox.plugins.backup_plugin.{__name__}")


class BackupView(ObjectView):
    queryset = models.Backup.objects.all()


class BackupListView(ObjectListView):
    queryset = models.Backup.objects.all()
    # narrow list to the most recent daily backups
    #queryset = models.Backup.objects.filter(
    #    created__date=models.Backup.objects.aggregate(max_date=Max('created__date'))['max_date'])
    table = tables.BackupTable
    filterset = filtersets.BackupFilterSet
    filterset_form = forms.BackupFilterForm

    def __init__(self, *args, **kwargs):
        super(BackupListView, self).__init__(*args, **kwargs)
        logger.info(models.Backup.objects.aggregate(max_date=Max('created__date'))['max_date'])


class BackupEditView(ObjectEditView):
    queryset = models.Backup.objects.all()
    form = forms.BackupForm


class BackupDeleteView(ObjectDeleteView):
    queryset = models.Backup.objects.all()


class BackupViewTab(ViewTab):
    def render(self, instance):
        # Display tab only if the following is true
        # probably will want to check the device role
        if not (instance.status == "active" and instance.primary_ip and
                instance.role and instance.role not in config.get('ignored_device_roles', [])):
            logger.info(f"instance: {instance.status}, {instance.primary_ip}, {instance.role}")
            return None
        return super().render(instance)


@register_model_view(Device, name="backup")
class DeviceBackupView(generic.ObjectView):
    """
    View for Device Backup Info.
    * This view will is rendered on the Device's Page Tab Menu.
    * Currently, no permissions are required -- all users will have this permission to the Tools
    """
    # additional_permissions = ["dcim.napalm_read_device"]
    queryset = Device.objects.all()
    template_name = "backup_plugin/device_backup.html"

    # define the View Tab
    tab = BackupViewTab(
        label='Latest Backup',
        # permission="dcim.napalm_read_device",
        weight=3200,
    )

    def get_extra_context(self, request, instance): # noqa
        backup_info = {}
        backup_data = []
        diff = None

        try:
            client = Client()
            backup_info = client.get_device_by_name(instance.name)
            if not backup_info:
                return {}

            info = client.get_device_latest_backup_diff(backup_info['id'])
            diff = info.get('diff')
            backup_data = info.get('backups')

        except Exception as e:
            logger.exception(e)

        return {
            'backup_info': backup_info,
            'backup_data': backup_data,
            'diff': diff,
        }

