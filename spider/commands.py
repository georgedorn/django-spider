from djutils.queue.decorators import queue_command, periodic_command, crontab

from spider.models import SpiderSession, SpiderProfile


@periodic_command(crontab(minute='*/30'))
def check_health():
    for profile in SpiderProfile.objects.all():
        profile.check_health()

@queue_command
def run_spider(session_id):
    session = SpiderSession.objects.get(pk=session_id)
    session.spider()
