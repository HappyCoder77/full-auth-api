from djoser import email


class ActivationEmail(email.ActivationEmail):
    template_name = 'users/activation.html'


class PasswordResetEmail(email.PasswordResetEmail):
    template_name = 'users/password_reset.html'
