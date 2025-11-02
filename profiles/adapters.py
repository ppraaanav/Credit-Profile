from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class CustomAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        """Redirect users after login based on their role"""
        # Check if redirect was set in session (from social login)
        redirect_url = request.session.get('login_redirect')
        if redirect_url:
            del request.session['login_redirect']
            return redirect_url
        
        if request.user.is_authenticated:
            if request.user.is_staff:
                return "/dashboard/"
            else:
                return "/my-dashboard/"
        return super().get_login_redirect_url(request)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def get_login_redirect_url(self, request):
        """Redirect after social login - always redirect based on user role"""
        # Always use role-based redirect, ignore any 'next' parameter
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Check if redirect was set in session (from pre_social_login signal)
            redirect_url = request.session.get('login_redirect')
            if redirect_url:
                del request.session['login_redirect']
                return redirect_url
            
            if request.user.is_staff:
                return "/dashboard/"
            else:
                return "/my-dashboard/"
        # If user not authenticated yet, return default but don't fall through
        return "/"
    
    def save_user(self, request, sociallogin, form=None):
        """Save new user from social login and set redirect"""
        user = super().save_user(request, sociallogin, form)
        # New users go to customer dashboard
        request.session['login_redirect'] = '/my-dashboard/'
        return user
    
    def get_connect_redirect_url(self, request, socialaccount):
        """Redirect after connecting social account"""
        if request.user.is_staff:
            return "/dashboard/"
        else:
            return "/my-dashboard/"

