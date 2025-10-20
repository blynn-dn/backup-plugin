from django.urls import path
from . import models, views
from netbox.views.generic import ObjectChangeLogView
from .models import Backup

urlpatterns = [
    path('backups/', views.BackupListView.as_view(), name='backup_list'),
    path("backup/<int:pk>/", views.BackupView.as_view(), name="backup"),
    path("backup/<int:pk>/edit", views.BackupEditView.as_view(), name="backup_edit"),
    path("backup/<int:pk>/delete", views.BackupDeleteView.as_view(), name="backup_delete"),
    path("backup/add", views.BackupView.as_view(), name="backup_add"),
    path(
        "backup/<int:pk>/changelog/", ObjectChangeLogView.as_view(), name="backup_changelog",
        kwargs={'model': Backup}
    ),
]
