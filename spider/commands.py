from djutils.queue.decorators import queue_command, periodic_command, crontab

from spider.models import SpiderSession


@periodic_command(crontab())
def check_health():
    pass

@queue_command
def run_spider(session_id):
    session = SpiderSession.objects.get(pk=session_id)
    session.spider()
