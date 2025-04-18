from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Plot, Field, Sensor, StatusHistory, Pump, PumpActionHistory

@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'total_area', 'owner', 'created_at')
    list_filter = ('owner',)
    search_fields = ('name', 'location')
    readonly_fields = ('created_at', 'map_preview')
    fieldsets = (
        (_('Asosiy ma\'lumot'), {
            'fields': ('name', 'location', 'total_area', 'owner')
        }),
        (_('Xarita'), {
            'fields': ('latitude', 'longitude', 'map_preview')
        }),
        (_('Tarix'), {
            'fields': ('created_at',)
        }),
    )

    def map_preview(self, obj):
        if obj.latitude and obj.longitude:
            return format_html(
                '<iframe width="100%" height="300" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" '
                'src="https://maps.google.com/maps?q={},{}&z=15&output=embed"></iframe>',
                obj.latitude, obj.longitude
            )
        return _("Koordinatalar ko'rsatilmagan")
    map_preview.short_description = _("Xarita ko'rinishi")

@admin.register(Plot)
class PlotAdmin(admin.ModelAdmin):
    list_display = ('name', 'field', 'crop_type', 'area', 'status_badge', 'is_active', 'current_moisture', 'current_temperature', 'updated_at')
    list_filter = ('field', 'status', 'is_active', 'crop_type', 'field__owner')
    search_fields = ('name', 'description', 'crop_type')
    readonly_fields = ('created_at', 'updated_at', 'status_badge', 'current_moisture', 'current_temperature', 'sensor_data_link')
    fieldsets = (
        (_('Asosiy ma\'lumot'), {
            'fields': ('field', 'name', 'description', 'area', 'crop_type', 'is_active')
        }),
        (_('Holat'), {
            'fields': ('status_badge', 'current_moisture', 'current_temperature', 'updated_at')
        }),
        (_('Sensor ma\'lumotlari'), {
            'fields': ('sensor_data_link',)
        }),
        (_('Tarix'), {
            'fields': ('created_at',)
        }),
    )
    actions = ['update_status_from_sensors', 'activate_plots', 'deactivate_plots']
    
    def status_badge(self, obj):
        colors = {
            'yetarli': 'green',
            'ortacha': 'yellow',
            'sugorish_kerak': 'red'
        }
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; border-radius: 10px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = _("Holat")
    
    def current_moisture(self, obj):
        moisture = obj.get_current_moisture()
        if moisture is not None:
            color = 'green' if moisture >= 70 else 'yellow' if moisture >= 40 else 'red'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}%</span>',
                color, round(moisture, 1)
            )
        return _("Ma'lumot yo'q")
    current_moisture.short_description = _("Joriy namlik")
    
    def current_temperature(self, obj):
        temp = obj.get_current_temperature()
        if temp is not None:
            color = 'red' if temp > 30 else 'orange' if temp > 25 else 'green'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}°C</span>',
                color, round(temp, 1)
            )
        return _("Ma'lumot yo'q")
    current_temperature.short_description = _("Joriy harorat")
    
    def sensor_data_link(self, obj):
        url = f'/admin/irrigation/sensor/?plot__id__exact={obj.id}'
        return format_html(
            '<a href="{}" class="button">Sensor ma\'lumotlarini ko\'rish</a>',
            url
        )
    sensor_data_link.short_description = _("Sensor ma'lumotlari")
    
    def update_status_from_sensors(self, request, queryset):
        updated = 0
        for plot in queryset:
            old_status = plot.status
            plot.update_status_from_sensors()
            if old_status != plot.status:
                updated += 1
        
        if updated:
            self.message_user(request, _(f"{updated} ta maydonning holati yangilandi."))
        else:
            self.message_user(request, _("Maydonlar holati o'zgarmadi."))
    update_status_from_sensors.short_description = _("Holatni sensorlar ma'lumotlari asosida yangilash")
    
    def activate_plots(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, _(f"{queryset.count()} ta maydon faollashtirildi."))
    activate_plots.short_description = _("Tanlangan maydonlarni faollashtirish")
    
    def deactivate_plots(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, _(f"{queryset.count()} ta maydon faolsizlantirildi."))
    deactivate_plots.short_description = _("Tanlangan maydonlarni faolsizlantirish")

@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    list_display = ('plot', 'sensor_type', 'value_with_unit', 'timestamp')
    list_filter = ('sensor_type', 'plot__field', 'plot')
    search_fields = ('plot__name', 'plot__field__name')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    
    def value_with_unit(self, obj):
        unit = '%' if obj.sensor_type == 'humidity' else '°C'
        color = ''
        if obj.sensor_type == 'humidity':
            color = 'green' if obj.value >= 70 else 'yellow' if obj.value >= 40 else 'red'
        elif obj.sensor_type == 'temperature':
            color = 'red' if obj.value > 30 else 'orange' if obj.value > 25 else 'green'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}{}</span>',
            color, obj.value, unit
        )
    value_with_unit.short_description = _("Qiymat")
    value_with_unit.admin_order_field = 'value'

@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('plot', 'status_badge', 'moisture_level', 'temperature', 'timestamp')
    list_filter = ('status', 'plot__field', 'plot')
    search_fields = ('plot__name', 'plot__field__name')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    
    def status_badge(self, obj):
        colors = {
            'yetarli': 'green',
            'ortacha': 'yellow',
            'sugorish_kerak': 'red'
        }
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; border-radius: 10px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = _("Holat")

@admin.register(Pump)
class PumpAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active_badge', 'speed_with_unit', 'last_status_change', 'serving_fields_list')
    list_filter = ('is_active', 'serving_fields')
    search_fields = ('name', 'serving_fields__name')
    readonly_fields = ('last_status_change',)
    filter_horizontal = ('serving_fields',)
    
    def is_active_badge(self, obj):
        color = 'green' if obj.is_active else 'red'
        text = _("Yoqilgan") if obj.is_active else _("O'chirilgan")
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; border-radius: 10px;">{}</span>',
            color, text
        )
    is_active_badge.short_description = _("Holat")
    
    def speed_with_unit(self, obj):
        return f"{obj.speed}% ({obj.speed_lps} l/s)"
    speed_with_unit.short_description = _("Tezlik")
    
    def serving_fields_list(self, obj):
        return ", ".join([field.name for field in obj.serving_fields.all()])
    serving_fields_list.short_description = _("Xizmat ko'rsatadigan dalalar")

@admin.register(PumpActionHistory)
class PumpActionHistoryAdmin(admin.ModelAdmin):
    list_display = ('pump', 'action_display', 'timestamp')
    list_filter = ('action', 'pump')
    search_fields = ('pump__name',)
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    
    def action_display(self, obj):
        colors = {
            'activated': 'green',
            'deactivated': 'red'
        }
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; border-radius: 10px;">{}</span>',
            colors.get(obj.action, 'gray'),
            obj.get_action_display()
        )
    action_display.short_description = _("Harakat")