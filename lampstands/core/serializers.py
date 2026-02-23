import logging
from rest_framework import serializers
from .models import ChurchPage, ChurchIndexPage
from django_countries.serializer_fields import CountryField

logger = logging.getLogger(__name__)

class LocalitiesSerializer(serializers.Serializer):
    """
    Optimized serializer that works with dicts from values() queryset.
    Much faster than model instance serialization - avoids object overhead.
    """
    id = serializers.IntegerField(read_only=True)
    url = serializers.SerializerMethodField()
    locality_name = serializers.CharField(required=False, allow_blank=True, max_length=255, allow_null=True)
    meeting_address = serializers.CharField(required=False, allow_blank=True, max_length=255, allow_null=True)
    locality_state_or_province = serializers.CharField(required=False, allow_blank=True, max_length=255, allow_null=True)
    locality_country = CountryField(required=False, country_dict=True, allow_null=True)
    locality_phone_number = serializers.CharField(required=False, allow_blank=True, max_length=255, allow_null=True)
    locality_email = serializers.EmailField(required=False, allow_blank=True, max_length=255, allow_null=True)
    locality_web = serializers.CharField(required=False, allow_blank=True, allow_null=True, style={'base_template': 'textarea.html'})
    location = serializers.SerializerMethodField()
    trimmed_address = serializers.SerializerMethodField()
    locality_contact_brother_1 = serializers.CharField(required=False, allow_blank=True, max_length=255, allow_null=True)
    locality_contact_brother_1_phone = serializers.CharField(required=False, allow_blank=True, max_length=25, allow_null=True)
    locality_contact_brother_2 = serializers.CharField(required=False, allow_blank=True, max_length=255, allow_null=True)
    locality_contact_brother_2_phone = serializers.CharField(required=False, allow_blank=True, max_length=25, allow_null=True)
    locality_contact_brother_3 = serializers.CharField(required=False, allow_blank=True, max_length=255, allow_null=True)
    locality_contact_brother_3_phone = serializers.CharField(required=False, allow_blank=True, max_length=25, allow_null=True)
    locality_contact_brother_4 = serializers.CharField(required=False, allow_blank=True, max_length=255, allow_null=True)
    locality_contact_brother_4_phone = serializers.CharField(required=False, allow_blank=True, max_length=25, allow_null=True)
    locality_contact_brother_5 = serializers.CharField(required=False, allow_blank=True, max_length=255, allow_null=True)
    locality_contact_brother_5_phone = serializers.CharField(required=False, allow_blank=True, max_length=25, allow_null=True)
    locality_contact_brother_6 = serializers.CharField(required=False, allow_blank=True, max_length=255, allow_null=True)
    locality_contact_brother_6_phone = serializers.CharField(required=False, allow_blank=True, max_length=25, allow_null=True)
    
    def get_url(self, obj):
        """Return the Wagtail page URL as an absolute URL.
        Works with dict from values() queryset - obj is a dict, not a model instance.
        Returns absolute URL for API responses (needed for JavaScript/frontend consumption).
        """
        request = self.context.get('request')
        slug = obj.get('slug', '')
        page_url = f'/churches/{slug}/' if slug else '/churches/'
        
        # Build absolute URL if request context is available (API responses)
        if request:
            return f"{request.scheme}://{request.get_host()}{page_url}"
        
        # Fallback to relative if no request context
        return page_url
    
    def get_location(self, obj):
        """Return location as a dict with numeric latitude and longitude.
        Works with dict from values() queryset.
        Supports legacy "lat,lng" and wagtail-geo-widget GEOSGeometry.
        """
        from lampstands.core.fields import parse_position_to_lat_lng
        position = obj.get('position')
        lat, lng = parse_position_to_lat_lng(position)
        return {"latitude": lat, "longitude": lng}
    
    def get_trimmed_address(self, obj):
        """Return URL-encoded meeting address.
        Works with dict from values() queryset.
        """
        from urllib.parse import quote
        meeting_address = obj.get('meeting_address')
        if meeting_address:
            return quote(meeting_address)
        return ""

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
