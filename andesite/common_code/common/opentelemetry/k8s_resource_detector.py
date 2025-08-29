import os
from urllib import parse

from opentelemetry.sdk.resources import Resource, ResourceDetector
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry_resourcedetector_kubernetes import Attributes

from common.jsonlogging.jsonlogger import Logging

logger = Logging.get_logger(__name__)


class KubernetesEnvResourceDetector(ResourceDetector):
    """
    Detects resource attributes for Kubernetes environments based on environment
    variables using a specified prefix.

    Note: The open source version of this does not work on reliably and appears abandoned:
    https://github.com/chrisguidry/opentelemetry-resourcedetector-kubernetes.
    Doesn't work since it relies on reading /proc/self/cgroup, which is not accessible in all containers / environments.
    We rely on environment variables being injected as part of the spec / helm chart instead.

    This class is responsible for extracting resource attributes relevant to
    Kubernetes environments from environment variables that are prefixed with
    a defined string. The attributes are mapped to their corresponding constants
    if they match certain predefined detectable names. It ensures compatibility with
    the OpenTelemetry semantic conventions for Kubernetes resource detection and can
    be used to seamlessly integrate resource discovery into telemetry systems.

    :ivar DETECTABLE: A dictionary mapping detectable constants from ResourceAttributes
        to their corresponding attribute names if the constants start with 'K8S_' or 'CONTAINER_'.
    :type DETECTABLE: Dict[str, str]
    :ivar _prefix: The environment variable prefix used to filter resource attributes.
        Defaults to 'OTEL_RD_' unless another prefix is provided during initialization.
    :type _prefix: str
    """

    DETECTABLE = {
        constant: getattr(ResourceAttributes, constant)
        for constant in dir(ResourceAttributes)
        if constant.startswith(("K8S_", "CONTAINER_"))
    }

    def __init__(self, prefix="OTEL_RD", **kwargs):
        super().__init__(**kwargs)
        self._prefix = prefix + ("_" if not prefix.endswith("_") else "")

    def detect(self) -> "Resource":
        eligible_env_vars: Attributes = {
            key.replace(self._prefix, "", 1): parse.unquote(value.strip())
            for key, value in os.environ.items()
            if key.startswith(self._prefix)
        }

        attributes: Attributes = {
            self.DETECTABLE[key]: value for key, value in eligible_env_vars.items() if key in self.DETECTABLE
        }

        if not attributes:
            logger().warning(f"No eligible {self._prefix.upper()}_* environment variables found.")

        return Resource(attributes)
