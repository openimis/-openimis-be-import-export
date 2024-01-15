from django.apps import AppConfig

MODULE_NAME = "im_export"

# todo these variables should be in settings.py
DEFAULT_CFG = {
    'IMPORT_EXPORT_USE_TRANSACTIONS': False,
    'IMPORT_EXPORT_SKIP_ADMIN_LOG': False,
    'IMPORT_EXPORT_TMP_STORAGE_CLASS': 'import_export.tmp_storages.CacheStorage',
    'IMPORT_EXPORT_IMPORT_PERMISSION_CODE': '131000',
    'IMPORT_EXPORT_EXPORT_PERMISSION_CODE': '131000',
    'IMPORT_EXPORT_CHUNK_SIZE': '100',

    'im_export_date_format': '%m/%d/%Y',
}


class ImportExportConfig(AppConfig):
    name = MODULE_NAME

    # IMPORT_EXPORT_USE_TRANSACTIONS = False
    # IMPORT_EXPORT_SKIP_ADMIN_LOG = False
    # IMPORT_EXPORT_TMP_STORAGE_CLASS = None
    # IMPORT_EXPORT_IMPORT_PERMISSION_CODE = None
    # IMPORT_EXPORT_CHUNK_SIZE = 100

    im_export_date_format = None

    def _configure_permissions(self, cfg):
        # managed by django-import-export
        pass

    def ready(self):
        from core.models import ModuleConfiguration
        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self._configure_permissions(cfg)

        self.im_export_date_format = cfg['im_export_date_format']
