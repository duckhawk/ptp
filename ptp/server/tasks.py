from celery import shared_task


@shared_task
def example_task(x, y):
    """Пример задачи Celery: сложение двух чисел."""
    return x + y
