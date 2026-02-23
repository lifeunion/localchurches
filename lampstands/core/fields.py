import re

from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

# GEOSGeometry from wagtail-geo-widget: SRID=4326;POINT(lng lat)
_geos_point_re = re.compile(r'POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)', re.IGNORECASE)

color_re = re.compile(r'^[A-Fa-f0-9]{6}$')
color_validator = RegexValidator(
    color_re,
    _('Enter a valid color.'),
    'invalid'
)


class ColorField(models.CharField):
    default_validators = [color_validator]

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 6
        super(ColorField, self).__init__(*args, **kwargs)


def parse_position_to_lat_lng(position):
    """
    Parse position string to (latitude, longitude).
    Supports:
      - wagtail-geo-widget: "SRID=4326;POINT(lng lat)" (WKT, x=lng y=lat)
      - legacy: "lat,lng" or "lat, lng"
    Returns (lat, lng) or (None, None) if unparseable.
    """
    if not position or not isinstance(position, str):
        return (None, None)
    s = position.strip()
    if not s:
        return (None, None)
    # GEOSGeometry / WKT: POINT(lng lat)
    m = _geos_point_re.search(s)
    if m:
        try:
            lng = float(m.group(1))
            lat = float(m.group(2))
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                return (lat, lng)
        except (ValueError, IndexError):
            pass
        return (None, None)
    # Legacy "lat,lng"
    parts = s.split(',', 1)
    if len(parts) == 2:
        try:
            lat_str, lng_str = parts[0].strip(), parts[1].strip()
            if lat_str and lng_str:
                lat = float(lat_str)
                lng = float(lng_str)
                if -90 <= lat <= 90 and -180 <= lng <= 180:
                    return (lat, lng)
        except (ValueError, TypeError):
            pass
    return (None, None)


class GeopositionField(models.CharField):
    """
    Simple replacement for django-geoposition's GeopositionField.
    Stores latitude and longitude as comma-separated "lat,lng" or
    wagtail-geo-widget GEOSGeometry string (SRID=4326;POINT(lng lat)).
    Use parse_position_to_lat_lng() to get (lat, lng) from either format.
    """
    description = _("A geoposition (latitude, longitude)")

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 250)  # GEOSGeometry strings need more than 42
        super(GeopositionField, self).__init__(*args, **kwargs)