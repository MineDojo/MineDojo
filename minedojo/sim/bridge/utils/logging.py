import logging
import threading


class QueueLogger(logging.StreamHandler):
    def __init__(self, queue):
        self._queue = queue
        super().__init__(None)

    def flush(self):
        pass

    def emit(self, record):
        self._queue.append((self.level, record))


def launch_queue_logger_thread(output_producer, should_end):
    def queue_logger_thread(out_prod, should_end):
        while not should_end():
            try:
                line, running = out_prod.get_output()
                if not running:
                    break
                if line:
                    level = line[0]
                    record = line[1]
                    name = line[2]
                    lgr = logging.getLogger(name)
                    lgr.log(level, record)
            except Exception as e:
                print(e)
                break

    thread = threading.Thread(
        target=queue_logger_thread, args=(output_producer, should_end)
    )
    thread.setDaemon(True)
    thread.start()
