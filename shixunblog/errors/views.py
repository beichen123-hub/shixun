from django.shortcuts import render

# Create your views here.
def not_page_found(request, exception):
    return render(request, "404.html", exception)

def page_error(request):
    return render('500.html')