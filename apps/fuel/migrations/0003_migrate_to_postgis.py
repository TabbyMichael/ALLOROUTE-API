from django.db import migrations, models
import django.contrib.gis.db.models.fields
from django.contrib.gis.geos import Point

def migrate_lat_lng_to_point(apps, schema_editor):
    FuelStation = apps.get_model("fuel", "FuelStation")
    for station in FuelStation.objects.all():
        if station.latitude and station.longitude:
            station.location = Point(station.longitude, station.latitude)
            station.save()

class Migration(migrations.Migration):

    dependencies = [
        ("fuel", "0002_alter_fuelstation_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="fuelstation",
            name="location",
            field=django.contrib.gis.db.models.fields.PointField(
                geography=True, help_text="GIS location (lng, lat)", srid=4326, null=True
            ),
        ),
        migrations.RunPython(migrate_lat_lng_to_point, reverse_code=migrations.RunPython.noop),
        migrations.RemoveIndex(
            model_name="fuelstation",
            name="fuel_fuelst_latitud_e7de73_idx",
        ),
        migrations.RemoveField(
            model_name="fuelstation",
            name="latitude",
        ),
        migrations.RemoveField(
            model_name="fuelstation",
            name="longitude",
        ),
        migrations.AlterField(
            model_name="fuelstation",
            name="location",
            field=django.contrib.gis.db.models.fields.PointField(
                geography=True, help_text="GIS location (lng, lat)", srid=4326
            ),
        ),
    ]
