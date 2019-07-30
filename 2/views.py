def moderator(function):
  @wraps(function)
  def wrap(request, *args, **kwargs):
      try:
        if request.user.is_moderator:
             return function(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(request.user.get_absolute_url())
      except:
          try:
              return HttpResponseRedirect(reverse('credits_list'))
          except AttributeError:
              return redirect(reverse('login'))
  return wrap


class ReviewCreateView(CreateView):
    model = Review
    form_class = ReviewCreateForm

    def get_initial(self):
        initial = super(ReviewCreateView, self).get_initial()
        initial.update({'name': self.request.user.get_full_name()})
        return initial

    def form_valid(self, form):
        review = form.save(commit=False)
        review.user = self.request.user
        review.save()
        return JsonResponse({'success': True, 'location': reverse('review_detail', kwargs={'pk': review.pk})})

    def form_invalid(self, form):
        errors = dict([(k, v[0]) for k, v in form.errors.items()])
        return JsonResponse({'success': False, 'errors': errors})


def get_city(request):
    if request.GET.get('city'):
        city = City.objects.filter(name=request.GET.get('city'))
        template_ajax = render_to_string(
            template_name='credits/includes/credits_filter_result.html',
            context={
        })
        return JsonResponse({'success': True, 'template': template_ajax, 'slug': city[0].slug})
    else:
        raise Http404
