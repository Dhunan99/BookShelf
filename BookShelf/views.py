from django.shortcuts import redirect
def redir(request):
    if request.user.is_authenticated:
        return redirect('/user/home')
    return redirect('/user/login')