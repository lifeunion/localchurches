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
        Build from slug only: /churches/{slug}/. Church pages are children of ChurchIndexPage
        at /churches/, so this matches the actual URL structure. Avoids any DB queries
        (get_url_parts/url each trigger ~1 query per record -> 1500+ queries for the list).
        """
        try:
            request = self.context.get('request')
            slug = getattr(obj, 'slug', None) or ''
            page_url = f'/churches/{slug}/' if slug else '/churches/'
            if request:
                return f"{request.scheme}://{request.get_host()}{page_url}"
            return page_url
        except Exception as e:
            logger.error(f"[LocalitiesSerializer] Error getting URL for id={getattr(obj, 'id', '?')}: {e}", exc_info=True)
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
