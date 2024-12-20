from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task()
def test_task():
    logger.info("Ejecutando test task")


@shared_task
def my_periodic_task():
    try:
        logger.info("Ejecutando tarea periódica")

    except Exception as e:
        logger.error(f"Error en la tarea periódica: {str(e)}")
        raise
