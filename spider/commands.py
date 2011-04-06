from django.conf import settings
from django.core.mail import mail_admins
from django.template.loader import render_to_string

from spider.models import SpiderSession, SpiderProfile

from djutils.queue.decorators import queue_command, periodic_command, crontab


# by default do not send emails
EMAIL_STATUS_CHECK = getattr(settings, 'SPIDER_EMAIL_STATUS_CHECK', False) 

@periodic_command(crontab(minute='*/30'))
def check_health():
    errors = []
    for profile in SpiderProfile.objects.all():
        status_check = profile.check_health()
        if not status_check.is_ok():
            errors.append(status_check)
    
    if errors and EMAIL_STATUS_CHECK:
        message = render_to_string('spider/email/status_check.txt', {
            'status_check_list': errors
        })
        mail_admins('Spider status check error email', message.strip(), fail_silently=True)

@queue_command
def run_spider(session_id):
    session = SpiderSession.objects.get(pk=session_id)
    session.spider()
