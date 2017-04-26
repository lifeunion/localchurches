from rest_framework import serializers
from .models import ChurchPage
from django_countries.serializer_fields import CountryField

class LocalitiesSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=False)
    locality_name = serializers.CharField(required=True, allow_blank=True, max_length=255)
    meeting_address = serializers.CharField(required=True, allow_blank=True, max_length=255)
    locality_state_or_province = serializers.CharField(required=True, allow_blank=True, max_length=255)
    locality_country = CountryField(required=True)
    locality_phone_number = serializers.CharField(required=False, allow_blank=True, max_length=255)
    locality_email = serializers.EmailField(required=False, allow_blank=True, max_length=255)
    locality_web = serializers.CharField(style={'base_template': 'textarea.html'}) 

    class Meta:
        model = ChurchPage
        fields = ('url','id','locality_name', 'meeting_address', 'locality_state_or_province', 
            'locality_country', 'locality_phone_number', 'locality_email','locality_web')

    def create(self, validated_data):
        """
        Create and return a new `localities` instance, given the validated data.
        """
        return ChurchIndexPage.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing `localities` instance, given the validated data.
        """
        instance.locality_name = validated_data.get('locality_name', instance.locality_name)
        instance.meeting_address = validated_data.get('meeting_address', instance.meeting_address)
        instance.locality_state_or_province = validated_data.get('locality_state_or_province', instance.locality_state_or_province)
        instance.locality_country = validated_data.get('locality_country', instance.locality_country)
        instance.position = validated_data.get('position', instance.position)
        instance.locality_phone_number = validated_data.get('locality_phone_number', instance.locality_phone_number)
        instance.locality_email = validated_data.get('locality_email', instance.locality_email)
        instance.locality_web = validated_data.get('locality_web', instance.locality_web)
        instance.save()
        return instance