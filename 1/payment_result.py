def result(request):
    template = 'payments/result.html'
    ctx = {}

    logger.debug(u"/payments/result/ POST: %s" % str(request.POST.dict()))
    logger.debug(u"/payments/result/ request: %s" % str(request))

    invoice = Invoice.objects.filter(user=request.user).last()

    #Settings of merchant
    settings_options = get_options()
    merchant = settings_options.get('merchant', None)
    merchant_id = merchant.get('merchant_id', None)
    if merchant_id is None:
        raise ImproperlyConfigured("Option FONDY_OPTIONS['merchant']['merchant_id'] must be set in your settings.py file.")
    secret_key = merchant.get('secret_key', None)
    if secret_key is None:
        raise ImproperlyConfigured("Option FONDY_OPTIONS['merchant']['secret_key'] must be set in your settings.py file.")
    options = settings_options.get('defaults', None)
    if options is None:
        raise ImproperlyConfigured("Option FONDY_OPTIONS['defaults'] must be set in your settings.py file.")

    if invoice.order.joint_product:
        return result_jp(request, invoice, merchant_id, secret_key, options)

    provider = Bill.objects.filter(order=invoice.order).last().recipient

    #Bonus for platform, in percent
    platform_percent = invoice.order.for_platform

    #Create invoice
    invoice_p2p = Invoice.objects.create(
        invoice_type = 'P2P',
        user=invoice.user,
        amount=int((invoice.amount - invoice.amount * platform_percent / 100) - invoice.amount * Decimal(AppConfig.objects.get(key='fondy_percent').value) / 2 / 100),
        currency='UAH',
        order=invoice.order,
        recipient=invoice.recipient,
    )

    #Parameters for signature (token) generating
    origin_params = {
        "order_id":str(invoice_p2p.payment_no),
        "order_desc":"order payment",
        "currency":invoice.currency,
        "amount":str(invoice_p2p.amount),
        "receiver_card_number":invoice.recipient.credit_card_number,
        "merchant_id":str(merchant_id)
    }

    #Generate signature (token)
    s = 'testcredit|'
    for i in sorted(origin_params):
        if origin_params[i]:
            s += origin_params[i] + '|'
    s = s[:-1]

    result = hashlib.sha1(s)
    signature = result.hexdigest()

    #Parameters for api request
    req = {
        "request": {
            "order_id": str(invoice_p2p.payment_no),
            "order_desc":"order payment",
            "currency":invoice.currency,
            "amount": str(invoice_p2p.amount),
            "receiver_card_number":invoice.recipient.credit_card_number,
            "signature": signature,
            "merchant_id":str(merchant_id)
            }
        }

    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    response = requests.post('https://api.fondy.eu/api/p2pcredit/', json=req, headers=headers)

    #api integration
    integration = FondyIntegration()
    data, trans, _res = integration.get_transaction(request, signature, origin_params)
    order_id = trans.order_id

    #If the payment was successful, I make changes to the invoice,
    #send a message to the provider about the payment.
    if _res == 'CREATED':
        ctx['data'] = request.POST.copy().items()
        percent = invoice.amount / invoice.order.products_cost

        if invoice.order.prepayment_paid < invoice.order.prepayment_perc:
            if (invoice.order.prepayment_paid + Decimal(percent)) > invoice.order.prepayment_perc:
                rest = invoice.order.prepayment_perc - invoice.order.prepayment_paid
                percent -= rest
                invoice.order.prepayment_paid = invoice.order.prepayment_perc
            else:
                invoice.order.prepayment_paid += Decimal(percent)
                percent = Decimal(0.00)
        invoice.order.prepayment_rest = invoice.order.prepayment_perc - invoice.order.prepayment_paid
        count = Decimal(percent * invoice.order.products_cost / 100)
        invoice.order.prepayment_rest_in_curr = invoice.order.prepayment_rest * invoice.order.products_cost / 100
        invoice.order.postpayment_paid += percent
        invoice.order.postpayment_rest = round(100 - invoice.order.prepayment_perc - invoice.order.postpayment_paid, 2)
        invoice.order.postpayment_rest_in_curr = round(Decimal(invoice.order.postpayment_rest) * invoice.order.products_cost / 100, 2)
        invoice.order.save()


        adminid = AppConfig.objects.get(key='default_wallet_blago')
        admin = User.objects.get(id=adminid.value)
        subject = 'Сообщение об оплате заказа №{0}"'.format(
            invoice.order.id
        )
        date = '{:%d.%m.%Y в %H:%M}'.format(datetime.now() + timedelta(hours=3))
        content = (
            'Сообщение об оплате заказа №{0}. ({6})\n'
            'Дата оплаты - {1}.\n'
            'Сумма оплаты - {2} {3}.\n'
            'Пользователь - {4}. ({7})\n'
            'Тип оплаты - {5}.\n'
        ).format(invoice.order.id, date, invoice.amount/100, Currency.objects.filter(default=True)[0].sign, request.user, 'На карту', invoice.order.get_absolute_url(), request.user.get_absolute_url())
        Message.objects.create(
            sender=admin, recipient=invoice.order.provider.user,
            subject=subject, content=content
        )

        #If paid all amount
        if invoice.order.postpayment_rest <= 0:
            invoice.order.status = 'paid'
            invoice.order.save(update_fields=['status'])
            bill = Bill.objects.filter(order=invoice.order).last()
            bill.paid = True
            bill.save(update_fields=['paid'])
            user = bill.user
            first_name = user.first_name
            last_name = user.last_name

            adminid = AppConfig.objects.get(key='default_wallet_blago')
            admin = User.objects.get(id=adminid.value)
            currencyaccount_admin = CurrencyAccount.objects.filter(user=admin).filter(currency='BLAGO').last()
            try:
                currencyaccount = CurrencyAccount.objects.filter(user=user).get(currency='BLAGO')
            except ObjectDoesNotExist:
                currencyaccount = CurrencyAccount.objects.create(
                    user = user,
                    title = 'BLAGO',
                    currency='BLAGO'
                )
            if invoice.order.thanks_for_buying > 0:
                Emission.objects.create(
                    user = user,
                    initiator_id = user.id,
                    source = 'buying',
                    amount = float(invoice.order.thanks_for_buying*Currency.objects.get(code='BLG').rate)
                )

                AccountTransaction.objects.create(
                    type = 'refill',
                    user = admin,
                    initiator_id = '-',
                    amount = float(invoice.order.thanks_for_buying*Currency.objects.get(code='BLG').rate),
                    comment = "За оплату заказа №{} пользователем {} {}".format(invoice.order.id, first_name, last_name),
                    balance = currencyaccount_admin.balance + Decimal(invoice.order.thanks_for_buying*Currency.objects.get(code='BLG').rate),
                )
                currencyaccount_admin.balance = currencyaccount_admin.balance + Decimal(invoice.order.thanks_for_buying*Currency.objects.get(code='BLG').rate)
                currencyaccount_admin.save(update_fields=['balance'])

                AccountTransaction.objects.create(
                    type = 'withdraw',
                    user = admin,
                    initiator_id = admin.id,
                    amount = float(invoice.order.thanks_for_buying*Currency.objects.get(code='BLG').rate),
                    comment = "Перевод на счёт пользователя {} {}".format(first_name, last_name),
                    balance = currencyaccount_admin.balance - Decimal(invoice.order.thanks_for_buying*Currency.objects.get(code='BLG').rate),
                )
                currencyaccount_admin.balance = currencyaccount_admin.balance - Decimal(invoice.order.thanks_for_buying*Currency.objects.get(code='BLG').rate)
                currencyaccount_admin.save(update_fields=['balance'])
                AccountTransaction.objects.create(
                    type = 'refill',
                    amount = float(invoice.order.thanks_for_buying*Currency.objects.get(code='BLG').rate),
                    user = user,
                    initiator_id = user.id,
                    balance = currencyaccount.balance + Decimal(invoice.order.thanks_for_buying*Currency.objects.get(code='BLG').rate),
                    comment = "Благодарим за оплату заказа №{}!".format(invoice.order.id),
                )
                currencyaccount.balance = currencyaccount.balance + Decimal(invoice.order.thanks_for_buying*Currency.objects.get(code='BLG').rate)
                currencyaccount.save(update_fields=['balance'])
        #Redirect to the order page
        return redirect(invoice.order.get_absolute_url())

    return render(request, template, ctx)
