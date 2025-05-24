from django.urls import path
from main.views import show_main, autocomplete_suggestions, query_corrections_api

app_name = 'main'

urlpatterns = [
    path('', show_main, name='show_main'),
    path('api/autocomplete/', autocomplete_suggestions, name='autocomplete'),
    path('api/corrections/', query_corrections_api, name='corrections'),
]