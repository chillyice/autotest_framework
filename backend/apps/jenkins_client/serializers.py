from rest_framework import serializers


class CreateJobRequestSerializer(serializers.Serializer):
    job_name = serializers.CharField(max_length=128)
    description = serializers.CharField(required=False, allow_blank=True)
    suite = serializers.ChoiceField(choices=["all", "api", "ui"], default="all")
    api_base_url = serializers.CharField(required=False, allow_blank=True, default="")
    ui_base_url = serializers.CharField(required=False, allow_blank=True, default="")
    repo_url = serializers.CharField()
    repo_branch = serializers.CharField(max_length=64, default="main")
    git_creds = serializers.CharField(required=False, allow_blank=True, default="")


class TriggerBuildSerializer(serializers.Serializer):
    job_name = serializers.CharField(max_length=128)
    params = serializers.DictField(required=False)


class BuildStatusSerializer(serializers.Serializer):
    job_name = serializers.CharField(max_length=128)
    build_number = serializers.IntegerField()


class JobStatusSerializer(serializers.Serializer):
    job_name = serializers.CharField(max_length=128)
