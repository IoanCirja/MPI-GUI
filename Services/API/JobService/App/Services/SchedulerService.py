import asyncio
from typing import Dict

from starlette.background import BackgroundTasks

from JobService.App.Repositories.JobRepository import JobRepository
from JobService.App.DTOs.JobUploadDTO import JobUploadDTO

user_queues: Dict[str, asyncio.Queue] = {}
queue_locks: Dict[str, asyncio.Lock] = {}

class JobSchedulerService:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.repository = JobRepository(user_id)

        if user_id not in user_queues:
            user_queues[user_id] = asyncio.Queue()
            queue_locks[user_id] = asyncio.Lock()

    async def queue_job(self, job_id: str, job_data: JobUploadDTO, background_tasks: BackgroundTasks):
        await user_queues[self.user_id].put((job_id, job_data))

        if not queue_locks[self.user_id].locked():
            background_tasks.add_task(self.process_user_queue)

    async def process_user_queue(self):
        async with queue_locks[self.user_id]:
            queue = user_queues[self.user_id]

            while not queue.empty():
                job_id, job_data = await queue.get()
                await self.execute_job_in_background(job_id, job_data)
                queue.task_done()

    async def execute_job_in_background(self, job_id: str, job_data: JobUploadDTO):

        print(f"Executing job {job_id} for user {self.user_id}")
        await asyncio.sleep(3)
        print(f"Job {job_id} completed for user {self.user_id}")
