from netbox.plugins import PluginConfig


class BackupPluginConfig(PluginConfig):
    name = 'backup_plugin'
    verbose_name = 'Backup Plugin'
    description = 'Backup'
    version = '1.1.0'
    author = 'Bryan Lynn'
    author_email = 'bryankentlynn@gmail.com'
    base_url = 'backup-plugin'
    min_version = '4.0'
    required_settings = []
    default_settings = {
        'loud': False
    }
    caching_config = {
        '*': None
    }


config = BackupPluginConfig
