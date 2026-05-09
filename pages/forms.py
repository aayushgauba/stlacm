from django import forms


class MailingListSubscribeForm(forms.Form):
    first_name = forms.CharField(max_length=80)
    last_name = forms.CharField(max_length=80, required=False)
    email = forms.EmailField(max_length=254)

    # Honeypot field (bots often fill it). Hidden via CSS in the template.
    company = forms.CharField(max_length=200, required=False)

