from django.contrib import admin
from .models import VolunteerProfile, VolunteerOpportunity, VolunteerSignup, VolunteerAttendance, VolunteerMessage, VolunteerCertificate

admin.site.register([VolunteerProfile, VolunteerOpportunity, VolunteerSignup, VolunteerAttendance, VolunteerMessage, VolunteerCertificate])
