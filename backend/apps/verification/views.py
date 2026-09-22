from django.shortcuts import render


def nid_verification_page(request):
    return render(request, "apps.verification/nid-verification.html")