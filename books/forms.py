from django import forms
class BookForm(forms.Form):
    title = forms.CharField(max_length=200)
    author_name = forms.CharField(max_length=100)
    language_name = forms.CharField(max_length=50)
    isbn = forms.IntegerField(required=False)
    publication_date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    category = forms.CharField(max_length=100)
    description = forms.CharField(widget=forms.Textarea)
    price = forms.DecimalField(required=False)
    cover_image = forms.ImageField(required=False)