from django.contrib import admin
from .models import CustomUser, UploadedDataset

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    actions = ['delete_selected']  # Allow bulk delete

    # Add a link to edit the user in the list display
    def edit_link(self, obj):
        from django.utils.html import format_html
        return format_html('<a href="{}">Edit</a>', f'/admin/prediction/customuser/{obj.id}/change/')
    edit_link.short_description = 'Edit'

    list_display = ('id', 'username', 'email', 'is_active', 'is_staff', 'is_superuser', 'edit_link')

class UploadedDatasetAdmin(admin.ModelAdmin):
    list_display = ('id', )  # Add more fields if needed
    search_fields = ()
    # You can add more admin options here if you want to allow editing/deleting predictions

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(UploadedDataset, UploadedDatasetAdmin)