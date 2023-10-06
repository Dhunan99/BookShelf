from django import forms
from .models import Category,Review,Authors, Category, Languages
class BookForm(forms.Form):
    title = forms.CharField(max_length=200)
    author_name = forms.CharField(max_length=100)
    language_name = forms.CharField(max_length=50)
    isbn = forms.IntegerField(required=False)
    Publication_Year = forms.IntegerField(
        widget=forms.NumberInput(attrs={'placeholder': 'Year'}),
        min_value=1900,  
        max_value=2099
    )
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
    )
    description = forms.CharField(widget=forms.Textarea)
    price = forms.DecimalField(required=False)
    cover_image = forms.ImageField(required=False)
class CategoryForm(forms.Form):
    name = forms.CharField(max_length=100)

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['title', 'review', 'style_rating', 'story_rating', 'grammar_rating', 'character_rating', 'overall_rating']
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 5:
            raise forms.ValidationError("Title must be at least 5 characters long.")
        return title

    def clean_review(self):
        review = self.cleaned_data.get('review')
        # Split the review text into words and count them
        word_count = len(review.split())
        if word_count < 50:
            raise forms.ValidationError("Review must contain at least 50 words.")
        return review
    
class BookFilterForm(forms.Form):
    keyword = forms.CharField(label='Keyword', required=False)
    author_name = forms.ModelChoiceField(
        queryset=Authors.objects.all(),
        label='Author',
        required=False
    )
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    sorting_options = forms.ChoiceField(
        choices=(
            ('alphabetic', 'Alphabetic'),
            ('price', 'Price'),
        ),
        label='Sorting Options',
        required=False
    )
    publication_year_min = forms.IntegerField(
        label='Publication Year (Min)',
        required=False
    )
    publication_year_max = forms.IntegerField(
        label='Publication Year (Max)',
        required=False
    )
    language = forms.ModelChoiceField(
        queryset=Languages.objects.all(),
        label='Language',
        required=False
    )
    min_review_count = forms.IntegerField(
        label='Minimum Review Count',
        required=False
    )
    min_rating_value = forms.FloatField(
        label='Minimum Rating Value',
        required=False
    )