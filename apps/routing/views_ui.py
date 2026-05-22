from django.views.generic import TemplateView


class TripDashboardView(TemplateView):
    template_name = "trip_map.html"
