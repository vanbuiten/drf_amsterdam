import json

from django.test import TestCase
from datetime import date

from tests.serializers import (
    WeatherStationSerializer, TemperatureRecordSerializer)
from tests.models import WeatherStation, TemperatureRecord

from rest_framework.test import APIClient
from rest_framework.serializers import ModelSerializer
from datapunt_api.rest import DisplayField

# # fake requests
# See: https://stackoverflow.com/questions/34438290/
# from rest_framework.request import Request
# from rest_framework.test import APIRequestFactory
#
# factory = APIRequestFactory()
# request = factory.get('/')


class TestDisplayFieldSerializer(ModelSerializer):
    _display = DisplayField()

    class Meta:
        model = WeatherStation
        fields = '__all__'


class SerializerTest(TestCase):
    def setUp(self):
        ws = WeatherStation.objects.create(number=260)
        records = [
            {'station': ws, 'date': date(1901, 1, 1), 'temperature': '10.0'},
            {'station': ws, 'date': date(1901, 2, 1), 'temperature': '11.0'},
            {'station': ws, 'date': date(1901, 3, 1), 'temperature': '20.0'},
        ]
        for rs in records:
            TemperatureRecord.objects.create(**rs)

    def test_active(self):
        self.assertTrue(True)

    def test_cannot_serialize_without_request_context(self):
        qs = TemperatureRecord.objects.all()
        self.assertTrue(qs.count() == 3)

        # We need request in context to build hyperlinks for relations.
        with self.assertRaises(AssertionError):
            TemperatureRecordSerializer(qs, many=True).data

    def test_json_html(self):
        c = APIClient()
        response = c.get('/tests/')
        self.assertEqual(response.status_code, 200)

    def test_weatherstation_endpoint(self):
        c = APIClient()
        response = c.get('/tests/weatherstation/', format='json')
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)

        # check that the basics look good for list endpoint
        self.assertEqual(payload['count'], 1)
        self.assertEqual(len(payload['results']), 1)
        self.assertEqual(
            payload['_links']['self']['href'],
            'http://testserver/tests/weatherstation/'
        )

        # check that we can follow the link to the detail endpoint
        detail_page = payload['results'][0]['_links']['self']['href']

        response = c.get(detail_page, format='json')
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertEqual(
            payload['_links']['self']['href'],
            detail_page
        )
        self.assertEqual(payload['number'], 260)

    def test_hal_style_pagination(self):
        c = APIClient()
        response = c.get('/tests/weatherstation/', format='json')
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)

        self.assertIn('_links', payload)
        self.assertEqual(
            payload['_links']['self']['href'],
            'http://testserver/tests/weatherstation/'
        )
        self.assertEqual(payload['_links']['next']['href'], None)
        self.assertEqual(payload['_links']['previous']['href'], None)

    def test_display_field(self):
        ws = WeatherStation.objects.get(number__exact=260)
        serializer = TestDisplayFieldSerializer(ws)
        self.assertEquals(
            serializer.data['_display'],
            'DISPLAY FIELD CONTENT'
        )
