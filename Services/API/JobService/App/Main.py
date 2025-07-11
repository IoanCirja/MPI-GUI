import asyncio
import base64
import logging
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from AuthService.App.Services.AuthService import UserService
from JobService.App.Controllers.JobController import router
from JobService.App.DTOs.JobUploadDTO import JobUploadDTO
from JobService.App.Services.JobService import JobService
from pydantic import ValidationError

MONITOR_INTERVAL = 3
NODES = [f"c05-{str(i).zfill(2)}.cs.tuiasi.ro" for i in range(21)]
status_active_connections = []

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

app = FastAPI()

origins = [
    "http://localhost:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(monitor_pending_jobs())


async def monitor_pending_jobs():
    job_service = JobService(None)

    MAX_RUNNING_JOBS_PER_CLUSTER = 2
    MAX_NODE_USAGE_PER_CLUSTER = 50
    MAX_PENDING_JOBS_PER_CLUSTER = 50
    MAX_TOTAL_USAGE_PER_CLUSTER = 500


    while True:
        await asyncio.sleep(MONITOR_INTERVAL)

        logger.info(f'Monitoring...');

        try:
            pending_jobs = await job_service.get_all_pending_jobs()
            running_jobs = await job_service.get_all_running_jobs()

            quotas = await  job_service.get_quotas()
            cluster_usage = await  job_service.compute_cluster_usage()
            request_usage = await job_service.compute_request_usage()

            if MAX_RUNNING_JOBS_PER_CLUSTER <= len(running_jobs):
                logger.info(f'MAX_RUNNING_JOBS_PER_CLUSTER reached.');
                continue

            if MAX_PENDING_JOBS_PER_CLUSTER <= len(pending_jobs):
                logger.info(f'MAX_PENDING_JOBS_PER_CLUSTER reached.');
                continue

            if MAX_TOTAL_USAGE_PER_CLUSTER <= len(pending_jobs) + len(running_jobs):
                logger.info(f'MAX_TOTAL_USAGE_PER_CLUSTER reached.');
                continue

            job_started = False

            for job in pending_jobs:
                if job_started:
                    break
                try:
                    job_dto = JobUploadDTO(
                        jobName=job.get("jobName"),
                        jobDescription=job.get("jobDescription"),
                        beginDate=job.get("beginDate"),
                        endDate=job.get("endDate"),
                        fileName=job.get("fileName"),
                        fileContent=job.get("fileContent"),
                        hostFile=job.get("hostFile"),
                        hostNumber=job.get("hostNumber"),
                        numProcesses=job.get("numProcesses"),
                        allowOverSubscription=job.get("allowOverSubscription"),
                        environmentVars=job.get("environmentVars"),
                        displayMap=job.get("displayMap"),
                        rankBy=job.get("rankBy"),
                        mapBy=job.get("mapBy"),
                        status=job.get("status"),
                        output=job.get("output"),
                        alertOnFinish=job.get("alertOnFinish"),
                        user_id=job.get("user_id"),
                        userEmail=job.get("userEmail"),
                        timeout=job.get("timeout"),
                    )
                    node_request = {}
                    encoded_hostfile = job["hostFile"]
                    decoded_content = base64.b64decode(encoded_hostfile).decode("utf-8")
                    lines = decoded_content.splitlines()
                    for line in lines:
                        parts = line.split()
                        if len(parts) == 2 and "slots=" in parts[1]:
                            node = parts[0]
                            slots = int(parts[1].split("=")[1])
                            node_request[node] = slots

                    exceeds_node_limit = False
                    for node, slots in node_request.items():
                        current_usage = cluster_usage.get(node, {}).get("total", 0)
                        if current_usage + slots > MAX_NODE_USAGE_PER_CLUSTER:
                            logger.warning(f"Skipping job {job['_id']} - Node {node} exceeds usage limit ({current_usage} + {slots} > {MAX_NODE_USAGE_PER_CLUSTER})")
                            exceeds_node_limit = True
                            break

                    if exceeds_node_limit:
                        continue


                    # job_author = job.get("user_id")
                    # job_quotas = quotas.get(job_author)


                    asyncio.create_task(job_service.execute_job_in_background(str(job["_id"]), job_dto))
                    job_started = True
                except ValidationError as ve:
                    logger.error(f"Error constructing JobUploadDTO for job {job['_id']}: {ve}")
                except Exception as e:
                    logger.error(f"Unexpected error processing job {job['_id']}: {e}")
        except Exception as e:
            logger.error(f"Error in monitoring pending jobs: {str(e)}")


