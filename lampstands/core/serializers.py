import logging
from rest_framework import serializers
from .models import ChurchPage, ChurchIndexPage
from django_countries.serializer_fields import CountryField

logger = logging.getLogger(__name__)

class LocalitiesSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    url = serializers.SerializerMethodField()  # Override to use Wagtail page URL
    locality_name = serializers.CharField(required=False, allow_blank=True, max_length=255, allow_null=True)
    meeting_address = serializers.CharField(required=False, allow_blank=True, max_length=255, allow_null=True)
    locality_state_or_province = serializers.CharField(required=False, allow_blank=True, max_length=255, allow_null=True)
    locality_country = CountryField(required=False, country_dict=True, allow_null=True)
    locality_phone_number = serializers.CharField(required=False, allow_blank=True, max_length=255, allow_null=True)
    locality_email = serializers.EmailField(required=False, allow_blank=True, max_length=255, allow_null=True)
    locality_web = serializers.CharField(required=False, allow_blank=True, allow_null=True, style={'base_template': 'textarea.html'})
    #position = GeopositionField()

    location = serializers.SerializerMethodField()
    trimmed_address = serializers.ReadOnlyField()
    
    class Meta:
        model = ChurchPage
        fields = ('id', 'url','locality_name', 'meeting_address', 'locality_state_or_province', 
            'locality_country', 'locality_phone_number', 'locality_email','locality_web', 'location', 'trimmed_address')
    
    def get_url(self, obj):
        """Return the Wagtail page URL as an absolute URL.
        Optimized to minimize database queries by using get_url_parts() with only() fields.
        Falls back to url property if get_url_parts() fails (should be cached after first call).
        """
        try:
            request = self.context.get('request')
            
            # Try get_url_parts() first - it should work with path and slug from only()
            # and may use cached site information
            try:
                url_parts = obj.get_url_parts()
                if url_parts and url_parts[2]:  # Check if page_path exists
                    _, root_url, page_path = url_parts
                    page_url = page_path
                else:
                    # If get_url_parts() returns None or empty path, use url property
                    # This is a @cached_property so subsequent calls are fast
                    page_url = obj.url
            except (AttributeError, Exception) as e:
                # If get_url_parts() fails (e.g., missing fields), use url property
                # This should work even with only() as url is a cached property
                page_url = obj.url
            
            # Ensure it starts with /
            if page_url and not page_url.startswith('/'):
                page_url = '/' + page_url
            
            # If we have a request, build absolute URL
            if request:
                absolute_url = f"{request.scheme}://{request.get_host()}{page_url}"
                return absolute_url
            else:
                return page_url
        except Exception as e:
            logger.error(f"[LocalitiesSerializer] Error getting URL for id={obj.id}: {e}", exc_info=True)
            # Final fallback: try to build from slug (last resort)
            try:
                if hasattr(obj, 'slug') and obj.slug:
                    page_url = f'/{obj.slug}/'
                    request = self.context.get('request')
                    if request:
                        return f"{request.scheme}://{request.get_host()}{page_url}"
                    return page_url
            except Exception:
                pass
            return None
    
    def get_location(self, obj):
        """Return location as a dict with numeric latitude and longitude.
        Optimized to parse position string only once instead of twice.
        Logging is conditional to reduce overhead in production.
        """
        if not obj.position:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"[LocalitiesSerializer] No position for id={obj.id}")
            return {"latitude": None, "longitude": None}
        
        try:
            # Parse position string once (instead of calling get_latitude_location/get_longitude_location separately)
            parts = obj.position.split(',')
            if len(parts) >= 2:
                lat_str = parts[0].strip()
                lng_str = parts[1].strip()
                
                if lat_str and lng_str:
                    lat = float(lat_str)
                    lng = float(lng_str)
                    
                    # Validate that coordinates are within valid ranges
                    if -90 <= lat <= 90 and -180 <= lng <= 180:
                        if logger.isEnabledFor(logging.DEBUG):
                            logger.debug(f"[LocalitiesSerializer] Parsed location for id={obj.id}: lat={lat}, lng={lng}")
                        return {"latitude": lat, "longitude": lng}
                    else:
                        logger.warning(f"[LocalitiesSerializer] Coordinates out of range for id={obj.id}: lat={lat}, lng={lng}")
        except (ValueError, TypeError, AttributeError, IndexError) as e:
            # Invalid position format - return None values
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"[LocalitiesSerializer] Error parsing position for id={obj.id}, position='{obj.position}': {e}")
        
        return {"latitude": None, "longitude": None}

    def create(self, validated_data):
        """
        Create and return a new `localities` instance, given the validated data.
        """
        return ChurchPage.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing `localities` instance, given the validated data.
        """
        # url is a read-only property from Wagtail Page model, don't try to set it
        instance.locality_name = validated_data.get('locality_name', instance.locality_name)
        instance.meeting_address = validated_data.get('meeting_address', instance.meeting_address)
        instance.locality_state_or_province = validated_data.get('locality_state_or_province', instance.locality_state_or_province)
        instance.locality_country = validated_data.get('locality_country', instance.locality_country)
        instance.position = validated_data.get('position', instance.position)
        instance.locality_phone_number = validated_data.get('locality_phone_number', instance.locality_phone_number)
        instance.locality_email = validated_data.get('locality_email', instance.locality_email)
        instance.locality_web = validated_data.get('locality_web', instance.locality_web)
        #instance.position = validated_data.get('position', instance.position)
        # location and trimmed_address are read-only properties, don't try to set them
        instance.save()
        return instance
