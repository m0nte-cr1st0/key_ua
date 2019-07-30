from fondy import get_fondy_transaction_model


TransactionModel = get_fondy_transaction_model()

logger = logging.getLogger('app')

class FondyIntegration(object):
    def __init__(self, params=None):
        # read settings options
        settings_options = get_options()
        merchant = settings_options.get('merchant', None)
        if merchant is None:
            raise ImproperlyConfigured("Option FONDY_OPTIONS['merchant'] must be set in your settings.py file.")
        merchant_id = merchant.get('merchant_id', None)
        if merchant_id is None:
            raise ImproperlyConfigured("Option FONDY_OPTIONS['merchant']['merchant_id'] must be set in your settings.py file.")
        secret_key = merchant.get('secret_key', None)
        if secret_key is None:
            raise ImproperlyConfigured("Option FONDY_OPTIONS['merchant']['secret_key'] must be set in your settings.py file.")
        api_protocol = merchant.get('api_protocol', None)
        if api_protocol is None:
            raise ImproperlyConfigured("Option FONDY_OPTIONS['merchant']['api_protocol'] must be set in your settings.py file.")
        self.options = settings_options.get('defaults', None)
        if self.options is None:
            raise ImproperlyConfigured("Option FONDY_OPTIONS['defaults'] must be set in your settings.py file.")

        self.api = Api(**merchant)
        self.merchant_id = merchant_id
        self.secret_key = secret_key
        self.api_protocol = api_protocol

        if params is None:
            params = {}
        self.options.update(params)

    def get_urls(self):
        urlpatterns = [
           url(r'^callback/$', self.callback, name="fondy_callback"),
        ]
        return urlpatterns

    def get_transaction(self, request, signature, origin):
        data = origin.copy()
        result = None
        trans = None
        if data:
            data = dict((k, v) for k, v in data.iteritems() if v not in (None, ''))
            data = OrderedDict(sorted(data.items()))

            result_signature = signature
            if 'response_signature_string' in data:
                del data['response_signature_string']

            if self.api.api_protocol == '2.0':
                str_sign = secret_key + '|'
                for i in sorted(dict(data)):
                    if data[i]:
                        str_sign += data[i] + '|'
                str_sign = str_sign[:-1]
                calc_sign = hashlib.sha1(str_sign).hexdigest()
            else:
                data = [secret_key]
                data.extend([str(params[key]) for key in sorted(iter(params.keys()))
                             if params[key] != '' and not params[key] is None])
                calc_sign = sha1(sep.join(data).encode('utf-8')).hexdigest()

            if signature == calc_sign:
                order_id = origin.get('order_id')
                try:
                    trans = TransactionModel.objects.get(order_id=order_id)
                    result = 'DETECTED'
                except TransactionModel.DoesNotExist:
                    trans = TransactionModel.objects.create(
                        payment_id=int(origin.get('order_id')),
                        order_id=order_id,
                        merchant_id=int(self.merchant_id),
                        amount=int(float(origin.get('amount'))),
                        currency=origin.get('currency'),
                        order_status='created',
                        tran_type="p2p transfer",
                        signature=request.POST.get('signature'),
                        raw_data=request.POST
                    )
                    result = 'CREATED'
                except Exception, e:
                    result = e.message.encode('utf-8')
        return data, trans, result

    def checkout_url(self):
        checkout = Checkout(api=self.api)
        d = self.options.copy()
        url = checkout.url(d).get('data')
        if url:
            url = json.loads(url)
            url = url.get('order')
            if url:
                url = url.get('checkout_url')
        return url

