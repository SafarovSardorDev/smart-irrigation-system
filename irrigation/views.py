from django.shortcuts import render
from django.utils import timezone
from .models import Pump, Plot, Sensor, StatusHistory
from django.db.models import Avg, Count
from datetime import timedelta
from django.db.models import Avg, Max, Min, Count
from django.views.generic import DetailView
from django.shortcuts import get_object_or_404



def home_view(request):
    # 1. Nasoslar ma'lumoti
    pumps = Pump.objects.all().order_by('id')[:2]  # Faqat 2 ta nasos
    
    # 2. Maydonlar ro'yxati (faqat faol maydonlar)
    plots = Plot.objects.filter(is_active=True).select_related('field')
    
    # 3. Sensor ma'lumotlari (24 soatlik)
    time_threshold = timezone.now() - timedelta(hours=24)
    
    # Namlik va harorat uchun o'rtacha qiymatlar
    active_plots = Plot.objects.filter(is_active=True)
    
    # Namlik statistikasi
    humidity_stats = Sensor.objects.filter(
        sensor_type='humidity',
        timestamp__gte=timezone.now()-timedelta(days=7)
    ).aggregate(
        avg_humidity=Avg('value'),
        max_humidity=Max('value'),
        min_humidity=Min('value')
    )
    
    # Harorat statistikasi (to'g'ri sintaksis)
    temperature_stats = Sensor.objects.filter(
        sensor_type='temperature',
        timestamp__gte=timezone.now()-timedelta(days=7)
    ).aggregate(
        avg_temp=Avg('value'),
        max_temp=Max('value'),
        min_temp=Min('value')
    )
    
    # Maydonlar holati bo'yicha statistika
    status_counts = Plot.objects.filter(is_active=True).values(
        'status').annotate(count=Count('id'))
    
    # Status stats ni dictionary ga o'tkazamiz
    status_stats = {
        'yetarli': 0,
        'ortacha': 0,
        'sugorish_kerak': 0
    }
    
    for item in status_counts:
        status_stats[item['status']] = item['count']

    context = {
        'pumps': pumps,
        'plots': plots,
        'humidity_stats': humidity_stats,
        'temperature_stats': temperature_stats,
        'status_stats': status_stats,
    }
    
    return render(request, 'home.html', context)


class PlotDetailView(DetailView):
    model = Plot
    template_name = 'plot_detail.html'
    context_object_name = 'plot'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plot = self.object
        
        # 1. Asosiy maydon ma'lumotlari
        context['field'] = plot.field
        context['crop_info'] = {
            'type': plot.crop_type,
            'planted_date': plot.created_at.strftime('%d/%m/%Y'),
            'area': f"{plot.area} gektar"
        }
        
        # 2. Hozirgi sensor ma'lumotlari
        context['current_stats'] = {
            'humidity': plot.get_current_moisture(),
            'temperature': plot.get_current_temperature(),
            'status': plot.get_status_display(),
            'status_class': plot.status  # rang uchun
        }
        
        # 3. Diagrammalar uchun ma'lumotlar (so'nggi 7 kun)
        time_threshold = timezone.now() - timedelta(days=7)
        
        # Harorat va namlik uchun kunlik o'rtachalar
        daily_stats = (
            Sensor.objects
            .filter(plot=plot, timestamp__gte=time_threshold)
            .extra({'date': "date(timestamp)"})
            .values('date', 'sensor_type')
            .annotate(
                avg_value=Avg('value'),
                max_value=Max('value'),
                min_value=Min('value')
            )
            .order_by('date')
        )
        
        # Diagrammalar uchun tayyorlash
        dates = []
        humidity_data = []
        temperature_data = []
        
        for day in range(7):
            date = (timezone.now() - timedelta(days=6-day)).date()
            dates.append(date.strftime('%d-%m'))
            
            hum = next((x for x in daily_stats 
                       if x['date'] == date and x['sensor_type'] == 'humidity'), None)
            humidity_data.append(hum['avg_value'] if hum else 0)
            
            temp = next((x for x in daily_stats 
                        if x['date'] == date and x['sensor_type'] == 'temperature'), None)
            temperature_data.append(temp['avg_value'] if temp else 0)
        
        context['chart_data'] = {
            'labels': dates,
            'humidity': humidity_data,
            'temperature': temperature_data,
            'humidity_min': min(humidity_data) if humidity_data else 0,
            'humidity_max': max(humidity_data) if humidity_data else 100,
            'temp_min': min(temperature_data) if temperature_data else 0,
            'temp_max': max(temperature_data) if temperature_data else 40,
        }
        
        # 4. Tarix jadvali uchun ma'lumotlar
        context['history'] = (
            StatusHistory.objects
            .filter(plot=plot)
            .select_related('plot')
            .order_by('-timestamp')[:20]  # So'nggi 20 ta yozuv
        )
        
        # 5. Xarita uchun ma'lumotlar
        context['map_data'] = {
            'coordinates': plot.field.location,
            'latitude': plot.field.latitude if hasattr(plot.field, 'latitude') else None,
            'longitude': plot.field.longitude if hasattr(plot.field, 'longitude') else None,
            'plot_name': plot.name,
            'field_name': plot.field.name
        }
        
        # 6. Bog'langan sensorlar
        context['sensors'] = (
            Sensor.objects
            .filter(plot=plot)
            .values('sensor_type')
            .annotate(count=Count('id'), last_seen=Max('timestamp'))
            .order_by('-last_seen')
        )
        
        return context
    