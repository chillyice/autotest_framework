from rest_framework import status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .client import JenkinsClient
from .serializers import (
    BuildStatusSerializer,
    CreateJobRequestSerializer,
    JobStatusSerializer,
    TriggerBuildSerializer,
)


class CreateJobView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = CreateJobRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        client = JenkinsClient()
        xml = client.render_job_xml(
            description=d["description"],
            suite=d["suite"],
            api_base_url=d["api_base_url"],
            ui_base_url=d["ui_base_url"],
            repo_url=d["repo_url"],
            repo_branch=d["repo_branch"],
            git_creds=d["git_creds"],
        )
        client.create_or_update_job(d["job_name"], xml)
        return Response({"job_name": d["job_name"], "ok": True})


class TriggerBuildView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = TriggerBuildSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        client = JenkinsClient()
        queue_id = client.trigger_build(d["job_name"], d.get("params") or {})
        return Response({"queue_id": queue_id, "job_name": d["job_name"]})


class BuildStatusView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ser = BuildStatusSerializer(data=request.query_params)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        client = JenkinsClient()
        info = client.get_build_info(d["job_name"], d["build_number"])
        return Response({
            "number": info.number,
            "result": info.result,
            "building": info.building,
            "duration_ms": info.duration_ms,
            "url": info.url,
        })


class JobInfoView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ser = JobStatusSerializer(data=request.query_params)
        ser.is_valid(raise_exception=True)
        job_name = ser.validated_data["job_name"]
        client = JenkinsClient()
        r = client._s.get(f"{client.base_url}/job/{job_name}/api/json")
        if not r.ok:
            return Response({"exists": False}, status=status.HTTP_404_NOT_FOUND)
        d = r.json()
        return Response({
            "exists": True,
            "name": d["name"],
            "url": d["url"],
            "in_queue": d.get("inQueue", False),
            "last_build": (d.get("lastBuild") or {}).get("number"),
            "last_result": (d.get("lastBuild") or {}).get("result"),
        })
