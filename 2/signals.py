#after registration

@receiver(post_save, sender=User)
def clearbit_api(instance, created, **kwargs):
    '''Verify email by EmailHunter & Getting data by email from `clearbit/enrichment`'''
    if created:
        clearbit.key = clearbit_key
        hunter = PyHunter(hunter_key)
        try:
            result = hunter.email_verifier(instance.email)
        except requests.exceptions.HTTPError:
            logger.exception('email {} not found'.format(instance.email))
            result = None
        #confirmed, if email is in the `emailhunter` database
        if result and result['result'] == 'risky':
            instance.is_confirmed=True
        try:
            response = clearbit.Enrichment.find(email=instance.email, stream=True)
        except requests.exceptions.HTTPError as err:
            return logger.exception('email {} not found'.format(instance.email))
        #if this person is in the clearbit database
        if response and response['person'] is not None:
            if response['person']['name']['givenName']:
                instance.first_name = response['person']['name']['givenName']
            if response['person']['name']['familyName']:
                instance.last_name = response['person']['name']['familyName']
            #etc...
        instance.save()
