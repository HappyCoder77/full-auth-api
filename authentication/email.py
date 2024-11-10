from djoser import email


class ActivationEmail(email.ActivationEmail):
    template_name = 'authentication/activation.html'


class PasswordResetEmail(email.PasswordResetEmail):
    template_name = 'authentication/password_reset.html'
