#base_model.py

class AbstractBasePayment(models.Model):
    currency = models.CharField(_('currency'), max_length=255, choices=CURRENCY_CHOICES, default=CURRENCY_KZT)
    amount_from = models.IntegerField(_('amount from'), blank=True, null=True)
    amount_to = models.PositiveIntegerField(_('amount to'), blank=True, null=True)
    amount_note = models.CharField(_('amount note'), blank=True, null=True, max_length=255)
    period_from = models.IntegerField(_('period from'), blank=True, null=True)
    period_to = models.PositiveIntegerField(_('period to'), blank=True, null=True)
    rate = models.DecimalField(_('rate'), max_digits=7, decimal_places=2)
    eair = models.DecimalField(_('eair'), max_digits=7, decimal_places=2)
    scheme_redemption = models.CharField(_('redemption'), max_length=255, choices=SCHEME_CHOICES, default=SCHEME_ANY)
    income_proof = models.CharField(_('proof'), max_length=255, choices=CONFIRMATION_CHOICES, default=CONFIRMATION_WITHOUT)
    income_proof_note = models.CharField(_('proof note'), blank=True, max_length=255)
    security = models.CharField(_('security'), max_length=255, choices=SECURITY_CHOICES, default=SECURITY_WITHOUT)
    security_note = models.CharField(_('security note'), blank=True, max_length=255)
    borrower_category = models.CharField(_('borrower category'), max_length=255, choices=BORROWER_CATEGORY_CHOICES, default=BORROWER_CATEGORY_CHOICES)
    borrower_category_note = models.CharField(_('borrower category note'), blank=True, max_length=255)
    credit_history = models.CharField(_('credit_history'), max_length=255, choices=CREDIT_HISTORY_CHOICES, default=CREDIT_HISTORY_ANY)
    comission_name_type = models.CharField(_('comission name type'), max_length=255, choices=COMISSION_TYPE_CHOICES, default=COMISSION_TYPE_CONSIDERATION, blank=True, null=True)
    comission_value = models.DecimalField(_('comission value'), max_digits=7, decimal_places=2, blank=True, null=True)
    comission_type = models.CharField(_('comission type'), max_length=255, choices=COMISSION_CHOICES, default=COMISSION_MONTHLY, blank=True, null=True)
    comission_lot_type = models.CharField(_('comission lot type'), max_length=255, choices=COMISSION_LOT_CHOICES, default=COMISSION_LOT_TENGE, blank=True, null=True)
    insurance_value = models.DecimalField(_('insurance value'), max_digits=7, decimal_places=2, blank=True, null=True)
    insurance_type = models.CharField(_('insurance type'), max_length=255, choices=INSURANCE_CHOICES, default=INSURANCE_AMOUNT, blank=True, null=True)

    class Meta:
        abstract = True


#models.py

class CreditPayment(AbstractBasePayment):
    credit = models.ForeignKey(Credit, verbose_name=_('credit'))

    class Meta:
        verbose_name = _('credit payment')
        verbose_name_plural = _('Credits payments')


class HypothecPayment(AbstractBasePayment):
    credit = models.ForeignKey(Hypothec, verbose_name=_('hypothec'))
    fee_initial = models.DecimalField(_('fee_initial'), max_digits=5, decimal_places=2, default=0,
        help_text=_('In percent, %'))

    class Meta:
        verbose_name = _('hypothec payment')
        verbose_name_plural = _('Hypothec payments')
