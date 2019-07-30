#forms.py (customizing admin form)

class ConditionAdminForm(forms.ModelForm):
    issue_form = forms.MultipleChoiceField(choices = ISSUE_CHOICES, label=_("issue form"))

    def __init__(self, *args, **kwargs):
        super(ConditionAdminForm, self).__init__(*args, **kwargs)
        obj = kwargs.get('instance')
        if obj:
            initial = [i for i in obj.issue_form.split(', ')]
            self.initial['issue_form'] = initial

    class Meta:
        model = CreditCondition
        fields = '__all__'

    def clean_issue_form(self):
        issue_form = self.cleaned_data['issue_form']
        if not issue_form:
            raise forms.ValidationError("...")

        issue_form = ', '.join(issue_form)
        return issue_form


#base_admin.py

class BaseCreditAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'slug', 'created_at', 'updated_at']
    list_display_links = ('slug',)
    fieldsets = [
        (None, {'fields': [('best', 'hot'), 'name', 'slug']}),
        ('SEO', {'fields': [('breadcrumbs',), ('meta_title',), ('meta_keywords',), ('meta_description',), ('short_description',)]})
    ]
    model = AbstractBaseProduct


#admin.py

class DepositAdmin(BaseCreditAdmin):
    inlines = [DepositActionInlineAdmin, DepositPaymentInlineAdmin, DepositConditionInlineAdmin]

    def get_list_display(self, request):
        list_display = copy.deepcopy(super(DepositAdmin, self).get_list_display(request))
        list_display.insert(2, 'bank')
        return list_display

    def get_fieldsets(self, request, obj=None):
        fieldsets = copy.deepcopy(super(DepositAdmin, self).get_fieldsets(request, obj))
        fieldsets[0][1]['fields'].insert(1, 'bank')
        return fieldsets
