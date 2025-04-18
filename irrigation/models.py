from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
import datetime

class Field(models.Model):
    """
    Field represents the larger agricultural area containing multiple plots
    """
    name = models.CharField(_('Dala nomi'), max_length=100)
    location = models.CharField(_('Manzil'), max_length=200)
    total_area = models.FloatField(_('Umumiy maydon (gektar)'), validators=[MinValueValidator(0.1)])
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fields')
    created_at = models.DateTimeField(_('Yaratilgan sana'), auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Dala')
        verbose_name_plural = _('Dalalar')


class Plot(models.Model):
    """
    Plot represents a small section of the larger agricultural field
    """
    STATUS_SUFFICIENT = 'yetarli'
    STATUS_MEDIUM = 'ortacha'
    STATUS_NEEDS_IRRIGATION = 'sugorish_kerak'
    
    STATUS_CHOICES = [
        (STATUS_SUFFICIENT, _('Yetarli')),
        (STATUS_MEDIUM, _('O\'rtacha')),
        (STATUS_NEEDS_IRRIGATION, _('Sug\'orish kerak')),
    ]
    
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='plots')
    name = models.CharField(_('Maydon nomi'), max_length=100)
    description = models.TextField(_('Tavsif'), blank=True)
    area = models.FloatField(_('Maydon (gektar)'), validators=[MinValueValidator(0.01)])
    crop_type = models.CharField(_('Ekin turi'), max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        _('Holat'), 
        max_length=20, 
        choices=STATUS_CHOICES,
        default=STATUS_SUFFICIENT
    )
    is_active = models.BooleanField(_('Faol'), default=True)
    
    def __str__(self):
        return f"{self.field.name} - {self.name}"
    
    def get_current_moisture(self):
        """Gets the latest moisture reading from sensors on this plot"""
        latest_sensor = self.sensors.filter(sensor_type='humidity').order_by('-timestamp').first()
        return latest_sensor.value if latest_sensor else None
    
    def get_current_temperature(self):
        """Gets the latest temperature reading from sensors on this plot"""
        latest_sensor = self.sensors.filter(sensor_type='temperature').order_by('-timestamp').first()
        return latest_sensor.value if latest_sensor else None
    
    def update_status_from_sensors(self):
        """Update plot status based on sensor data"""
        moisture = self.get_current_moisture()
        
        if moisture is None:
            return
            
        # Define thresholds for status determination
        if moisture >= 70:  # More than 70% moisture
            new_status = self.STATUS_SUFFICIENT
        elif 40 <= moisture < 70:  # Between 40% and 70% moisture
            new_status = self.STATUS_MEDIUM
        else:  # Less than 40% moisture
            new_status = self.STATUS_NEEDS_IRRIGATION
        
        # Only create history record if status changed
        if new_status != self.status:
            self.status = new_status
            self.save(update_fields=['status', 'updated_at'])
            
            # Create a status change history entry
            StatusHistory.objects.create(
                plot=self,
                status=self.status,
                moisture_level=moisture,
                temperature=self.get_current_temperature()
            )
            
            # Update pump statuses automatically
            Pump.update_pumps_from_plot_statuses()
    
    class Meta:
        verbose_name = _('Maydon')
        verbose_name_plural = _('Maydonlar')


class Sensor(models.Model):
    """
    Sensor data from plots (temperature and humidity)
    """
    SENSOR_TYPE_CHOICES = [
        ('temperature', _('Harorat')),
        ('humidity', _('Namlik')),
    ]
    
    plot = models.ForeignKey(Plot, on_delete=models.CASCADE, related_name='sensors')
    sensor_type = models.CharField(_('Sensor turi'), max_length=20, choices=SENSOR_TYPE_CHOICES)
    value = models.FloatField(_('Qiymat'))
    timestamp = models.DateTimeField(_('Vaqt'), auto_now_add=True)
    
    def __str__(self):
        return f"{self.plot.name} - {self.get_sensor_type_display()}: {self.value}"
    
    def save(self, *args, **kwargs):
        """Override save to update plot status when new sensor data is added"""
        super().save(*args, **kwargs)
        # Update plot status when new sensor data is saved
        if self.sensor_type == 'humidity':
            self.plot.update_status_from_sensors()
    
    class Meta:
        indexes = [
            models.Index(fields=['plot', 'sensor_type', '-timestamp']),
        ]
        verbose_name = _('Sensor ma\'lumoti')
        verbose_name_plural = _('Sensor ma\'lumotlari')


class Pump(models.Model):
    name = models.CharField(_('Nasos nomi'), max_length=100)
    is_active = models.BooleanField(_('Faol'), default=False)
    serving_fields = models.ManyToManyField(Field, related_name='pumps', blank=True)
    last_status_change = models.DateTimeField(_('Oxirgi holat o\'zgarishi'), auto_now_add=True)

    # ✅ YANGI: Tezlik foizda (0-100%)
    speed = models.FloatField(
        _('Tezlik (%)'),
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text=_('Nasos tezligi foizda')
    )

    @property
    def speed_lps(self):
        """Tezlikni litr/sekundga aylantiruvchi xususiyat (misol uchun 100% = 10 l/s)"""
        return round((self.speed / 100.0) * 10, 2)  # Misol: 100% = 10 l/s
    
    def __str__(self):
        status = _('Yoqilgan') if self.is_active else _('O\'chirilgan')
        return f"{self.name} - {status}"
    
    def activate(self):
        """Turn the pump on"""
        if not self.is_active:
            self.is_active = True
            self.last_status_change = datetime.datetime.now()
            self.save()
            PumpActionHistory.objects.create(
                pump=self,
                action='activated',
                timestamp=self.last_status_change
            )
    
    def deactivate(self):
        """Turn the pump off"""
        if self.is_active:
            self.is_active = False
            self.last_status_change = datetime.datetime.now()
            self.save()
            PumpActionHistory.objects.create(
                pump=self,
                action='deactivated',
                timestamp=self.last_status_change
            )
    
    @classmethod
    def update_pumps_from_plot_statuses(cls):
        """
        Update all pumps based on the current plot statuses
        
        Logic:
        - If any plot needs irrigation (STATUS_NEEDS_IRRIGATION) - both pumps should be on
        - If any plot is medium (STATUS_MEDIUM) - one pump should be on
        - If all plots are sufficient (STATUS_SUFFICIENT) - both pumps should be off
        """
        needs_irrigation = Plot.objects.filter(status=Plot.STATUS_NEEDS_IRRIGATION, is_active=True).exists()
        medium_status = Plot.objects.filter(status=Plot.STATUS_MEDIUM, is_active=True).exists()
        
        # Get exactly 2 pumps in the system, ordered by ID
        pumps = cls.objects.all().order_by('id')[:2]
        
        if needs_irrigation:
            # Both pumps on
            for pump in pumps:
                pump.activate()
        elif medium_status:
            # First pump on, second pump off
            for i, pump in enumerate(pumps):
                if i == 0:
                    pump.activate()
                else:
                    pump.deactivate()
        else:
            # All pumps off
            for pump in pumps:
                pump.deactivate()
    
    class Meta:
        verbose_name = _('Nasos')
        verbose_name_plural = _('Nasoslar')


class StatusHistory(models.Model):
    """
    Historical records of plot status changes
    """
    plot = models.ForeignKey(Plot, on_delete=models.CASCADE, related_name='status_history')
    timestamp = models.DateTimeField(_('Vaqt'), auto_now_add=True)
    status = models.CharField(_('Holat'), max_length=20, choices=Plot.STATUS_CHOICES)
    moisture_level = models.FloatField(_('Namlik darajasi'), null=True, blank=True)
    temperature = models.FloatField(_('Harorat'), null=True, blank=True)
    speed = models.FloatField(
        _('Tezlik (l/s)'), 
        default=0.0, 
        validators=[MinValueValidator(0.0)],
        help_text=_('Nasos tezligi litr/sekundda')
    )

    def __str__(self):
        return f"{self.plot.name} - {self.get_status_display()} - {self.timestamp}"
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = _('Holat tarixi')
        verbose_name_plural = _('Holat tarixi')


class PumpActionHistory(models.Model):
    """
    Historical records of pump activations and deactivations
    """
    ACTION_CHOICES = [
        ('activated', _('Yoqilgan')),
        ('deactivated', _('O\'chirilgan')),
    ]
    
    pump = models.ForeignKey(Pump, on_delete=models.CASCADE, related_name='action_history')
    action = models.CharField(_('Harakat'), max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(_('Vaqt'))
    
    def __str__(self):
        return f"{self.pump.name} - {self.get_action_display()} - {self.timestamp}"
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = _('Nasos harakati tarixi')
        verbose_name_plural = _('Nasos harakatlari tarixi')