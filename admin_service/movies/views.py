from django.shortcuts import render


def my_view(request):
    return render(
        request,
        "movies/index.html",
        {
            "foo": "bar",
        },
        content_type="application/xhtml+xml",
    )
