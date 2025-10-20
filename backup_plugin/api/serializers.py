from backup_plugin.models import Backup
from netbox.api.serializers import NetBoxModelSerializer


class BackupSerializer(NetBoxModelSerializer):

    class Meta:
        model = Backup
        fields = (
            'id', 'name',
        )
