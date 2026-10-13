from fastapi import BackgroundTasks


class FastAPIJobs:
    def __init__(self, background_tasks: BackgroundTasks):
        self.background_tasks = background_tasks

    def enqueue(self, function, *args, **kwargs):
        self.background_tasks.add_task(function, *args, **kwargs)
