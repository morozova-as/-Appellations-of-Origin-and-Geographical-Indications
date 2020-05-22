from django.contrib import admin
from .models import Manufacturers, GeoIndication
import sys
sys.path.insert(1, '..')
from define_class import define_class


class ManufacturersAdmin(admin.ModelAdmin):
    model = Manufacturers
    list_display = ['id', 'mainId', 'manufacturer', 'description', 'status', 'href']


class GeoIndicationAdmin(admin.ModelAdmin):
    model = GeoIndication
    list_display = ['id', 'name', 'description', 'status', 'href', 'geo_loc_original', 'target']

    def save_model(self, request, obj, form, change):
        if not obj.target:
            obj.target = define_class(obj.description)

        super().save_model(request, obj, form, change)

admin.site.register(Manufacturers, ManufacturersAdmin)
admin.site.register(GeoIndication, GeoIndicationAdmin)
