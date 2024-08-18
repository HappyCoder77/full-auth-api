from djoser import email


class ActivationEmail(email.ActivationEmail):
    print('activation class')
    template_name = 'users/activation.html'
