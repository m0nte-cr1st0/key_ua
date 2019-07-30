@login_required
def add_to_cart_view(request):
    #Get data from ajax
    product_slug = request.GET.get('product_slug')
    product_count = request.GET.get('product_count')
    total_in_main_curr = request.GET.get('total_in_main_curr')

    product = Product.objects.get(id=int(product_slug))
    product_cost = product.lot_cost

    # Get or create cart of current user
    user_cart = Cart.objects.get_or_create(user=request.user)

    #Update cart if product is in user_cart
    if product.id in user_cart.cart_item.values_list('product', flat=True):
        item = CartItem.objects.filter(cart=user_cart).get(product=product)
        if float(product_count) > 0:
            x = user_cart.cart_total - Decimal(item.total_in_main_curr)
            item.qty = product_count
            item.total_in_main_curr = total_in_main_curr
            item.save(update_fields=['qty', 'total_in_main_curr'])
            x += Decimal(item.total_in_main_curr)
            user_cart.cart_total = x
            user_cart.save(update_fields=['cart_total'])
        else:
            user_cart.cart_total -= Decimal(item.total_in_main_curr)
            user_cart.save(update_fields=['cart_total'])
            item.delete()
    else:
        if float(product_count) > 0:
            CartItem.objects.create(
                cart = user_cart,
                product = product,
                qty = product_count,
                total_in_main_curr = total_in_main_curr
            )
            user_cart.cart_total += Decimal(total_in_main_curr)
            user_cart.save(update_fields=['cart_total'])

    #json response to page, update included template
    if request.is_ajax():
        def_curr = Currency.objects.filter(default=True)[0]
        template_ajax = render_to_string(
            template_name='products/includes/basket.html',
            context={
                'cart_total': str(user_cart.cart_total) + ' ' + def_curr.sign,
                'user': request.user
            })
        return JsonResponse({'success': True, 'template': template_ajax})


class OrderDetail(DetailView):
    model = Order
    http_method_names = ['get', 'post']
    template_name = 'products/order_detail.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Some code...

        if request.is_ajax():
            template_ajax = ''
            if request.GET.get('action'):
                adminid = AppConfig.objects.get(key='default_wallet_blago')
                admin = User.objects.get(id=adminid.value)
                site = u'{scheme}://{host}'.format(
                    scheme=request.scheme,
                    host=request.get_host()
                )
                if request.GET.get('action') == 'confirmation':
                    self.object.confirmation_status = 'confirmed'
                    self.object.save()
                    subject = 'Сообщение о подтверждении заказа №{0}"'.format(
                        self.object.id
                    )
                    content = (
                        'Заказ №{0} подтверждён. ({1}{2})\n'
                    ).format(self.object.id, self.object.get_absolute_url(), site)
                    Message.objects.create(
                        sender=admin, recipient=self.object.user,
                        subject=subject, content=content
                    )
                    return JsonResponse({})

            #Load more comments
            elif request.GET.get('mode') == 'all':
                comments = comments_all
            else:
                comments = comments_last
            for comment in comments:
                template_comment = render_to_string(
                    template_name='communication/includes/comment_item.html',
                    context={'comment': comment}
                )
                template_ajax = '\n'.join([template_ajax, template_comment])
            return JsonResponse({"success": True, 'template': template_ajax})

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            self.object = self.get_object()

            if 'type' in request.POST:
                if request.POST.get('type') in ['btc', 'manually']:

                    # Some code ...

                elif request.POST.get('type') == 'blago':

                    # Some code ...

                elif request.POST.get('type') == 'fondy':
                    count = Decimal(request.POST.get('count'))
                    amount = Decimal(request.POST.get('inp'))
                    order = self.object

                    # Create invoise for payment
                    invoice = Invoice.objects.create(
                        invoice_type=INVOICE_TYPE.ORDER_PAY,
                        user=request.user,
                        amount=amount*100,
                        currency='UAH',
                        order=self.object,
                        recipient=self.object.provider,
                    )

                    # Parameters for api request
                    params = {
                        'order_id': invoice.payment_no,
                        "order_desc": "order payment",
                        "currency": invoice.currency,
                        "amount": int(invoice.amount + invoice.amount * Decimal(AppConfig.objects.get(key='fondy_percent').value) / 2 / 100),
                        "operation_id": invoice.payment_no,
                    }

                    integration = FondyIntegration(params)

                    # Redirect to payment page
                    redirect_to = integration.checkout_url()
                    if request.is_ajax():
                        return JsonResponse({
                            'redirect_to': redirect_to,
                        })

