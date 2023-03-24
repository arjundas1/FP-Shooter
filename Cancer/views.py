
from django.http import HttpResponseRedirect
from django.urls import reverse


def redirect_to_home(request):

    return HttpResponseRedirect(reverse('home:index'))