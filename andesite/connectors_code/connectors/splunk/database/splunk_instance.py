import asyncio
import json
import os
import ssl
from contextlib import suppress
from datetime import datetime, timedelta
from functools import wraps
from hashlib import md5
from typing import Any, Union
from urllib.parse import urlparse

import httpx
import splunklib.client  # type: ignore
from cachetools import TLRUCache, TTLCache
from common.jsonlogging.jsonlogger import Logging
from common.managers.dataset_structures.dataset_structure_manager import (
    DatasetStructureManager,
)
from common.utils.async_wrap import async_wrap, run_sync_in_executor
from opentelemetry import trace
from pydantic import BaseModel, SecretStr, ValidationError
from splunklib import results as splunklib_results
from splunklib.binding import handler  # type: ignore[import-untyped]
from splunklib.client import SavedSearch, Service


from connectors.metrics import ConnectorMetrics
from connectors.query_instance import QueryInstance
from connectors.splunk.database.saved_search import SplunkSavedSearch
from connectors.splunk.database.utils import change_authorization_token_type

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class SplunkAccessTokenError(ValueError):
    pass


class SplunkField(BaseModel):
    field_name: str
    example_value: str | None = None


class SplunkSearchStatus(BaseModel):
    sid: str | None = None
    progress: float = 0.0
    scan_count: int = 0
    event_count: int = 0
    result_count: int = 0
    elapsed_seconds: float = 0



access_token_cache_key = "splunk-access-token"

saved_search_cache: TTLCache[str, list[SplunkSavedSearch]] = TTLCache(maxsize=10, ttl=300)


class SplunkInstance(QueryInstance):
    """
    Splunk instance is used by retrievers to execute splunk queries against a Splunk instance.

    If no token is provided, we will attempt to retrieve an access token from it from a configured oauth host
    """

    def __init__(
        self,
        protocol: str,
        host: str,
        port: int,
        token: SecretStr | None,
        ssl_verification: bool,
        app: str = "-",
        field_cache_ttl_seconds: int = 60 * 60,
        search_cache_ttl_seconds: int = 60 * 10,
        notable_index: str = "notable",
        notable_write_index: str = "andesite_alerts",
        es: bool | None = False,
        mtls_client_cert_path: str | None = None,
        mtls_client_key_path: str | None = None,
        mtls_client_cert_data: SecretStr | None = None,
        mtls_client_key_data: SecretStr | None = None,
        token_oauth_hostname: str | None = None,
        token_oauth_client_id: SecretStr | None = None,
        token_oauth_client_secret: SecretStr | None = None,
        uri_add_prefix: str | None = None,
        use_mtls: bool | None = None,
    ):
        self._protocol = protocol
        self._host = host
        self._port = port
        self._token = token
        self._ssl_verification = ssl_verification
        self._app = app
        self._notable_index = notable_index
        self._notable_write_index = notable_write_index
        self._es = es
        self._mtls_client_cert_path = mtls_client_cert_path
        self._mtls_client_key_path = mtls_client_key_path
        self._mtls_client_cert_data = mtls_client_cert_data
        self._mtls_client_key_data = mtls_client_key_data
        self._token_oauth_hostname = token_oauth_hostname
        self._token_oauth_client_id = token_oauth_client_id
        self._token_oauth_client_secret = token_oauth_client_secret
        self._uri_add_prefix = uri_add_prefix

        self._context: ssl.SSLContext | None = self._init_sslcontext() if use_mtls else None

        def cache_ttu_field(_key, _value, now):
            return now + timedelta(seconds=field_cache_ttl_seconds)

        def cache_ttu_ss(_key, _value, now):
            return now + timedelta(seconds=search_cache_ttl_seconds)

        # A cache for the access token that will expire the token every set period + jitter
        def cache_ttu_access_token(_key, value, now):
            duration = value.get("expires_in", 60 * 60) * 0.8  # We will invalidate at 80% of the expiration
            return now + timedelta(seconds=duration)

        self._field_cache: TLRUCache[str, list[SplunkField]] = TLRUCache(
            maxsize=100,
            ttu=cache_ttu_field,
            timer=datetime.now,  # type: ignore[arg-type]
        )
        self._ss_cache = TLRUCache(maxsize=100, ttu=cache_ttu_ss, timer=datetime.now)  # type: ignore[arg-type]
        self._access_token_response_cache = TLRUCache(
            maxsize=1,
            ttu=cache_ttu_access_token,
            timer=datetime.now,  # type: ignore[arg-type]
        )
        self._client: Service = None  # Lazy initialization to ensure app can start without a connection

    def _init_sslcontext(self) -> ssl.SSLContext | None:
        if not self._mtls_client_cert_path or not self._mtls_client_key_path:
            logger().warning("attempting to initialize splunk sslcontext, but no cert/key paths provided")

            return None
        # these file writes are temporary until we are off of ECS
        if self._mtls_client_cert_data and self._mtls_client_key_data:
            logger().info("splunk mtls cert/key data found in env vars")
            logger().info("writing cert file")
            cert_file = os.open(
                path=self._mtls_client_cert_path,
                flags=(os.O_WRONLY | os.O_CREAT),
                mode=0o600,
            )
            with open(cert_file, "w") as cert:
                # HACK: we need to replace the html input escaped newlines if any exist
                cert.write(self._mtls_client_cert_data.get_secret_value().replace("\\n", "\n"))

            logger().info("writing key file")
            key_file = os.open(
                path=self._mtls_client_key_path,
                flags=(os.O_WRONLY | os.O_CREAT),
                mode=0o600,
            )
            with open(key_file, "w") as key:
                # HACK: we need to replace the html input escaped newlines if any exist
                key.write(self._mtls_client_key_data.get_secret_value().replace("\\n", "\n"))

        c = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
        c.load_cert_chain(
            certfile=self._mtls_client_cert_path,
            keyfile=self._mtls_client_key_path,
        )

        return c

    def get_token_from_oauth(self) -> SecretStr | None:
        logger().info("Splunk token not set, attempting to retrieve access token")
        if access_token_cache_key in self._access_token_response_cache:
            logger().info("Retrieved cached splunk access token")
            return SecretStr(self._access_token_response_cache[access_token_cache_key]["access_token"])

        if not self._token_oauth_hostname or not self._token_oauth_client_id or not self._token_oauth_client_secret:
            logger().warning("Missing required oauth configuration, cannot retrieve access token through oauth")
            raise SplunkAccessTokenError("Missing configuration; cannot retrieve access token")

        url = f"https://{self._token_oauth_hostname}/oauth/client_credential/accesstoken?grant_type=client_credentials"

        timeout_sec = 5
        retries = 4

        with httpx.Client(
            timeout=timeout_sec,
            verify=self._context if self._context else False,
            auth=httpx.BasicAuth(
                self._token_oauth_client_id.get_secret_value(),
                self._token_oauth_client_secret.get_secret_value(),
            ),
        ) as client:
            response = None
            while not response and retries > 0:
                try:
                    response = client.post(url)
                except httpx.TimeoutException as tme:
                    if retries > 0:
                        logger().warning("Retrying timed out request", exc_info=tme)
                        retries -= 1
                        continue
                    logger().error("Request timed out", exc_info=tme)
                    raise SplunkAccessTokenError("Request timed out retrieving splunk access token")
            if not response or response.status_code != 200:
                logger().error(
                    "Failed to receive splunk access token. Response status code: %s",
                    response.status_code if response else "unknown",
                )
                raise SplunkAccessTokenError("Unable to retrieve splunk access token")
            try:
                json_response = response.json()
                self._access_token_response_cache[access_token_cache_key] = json_response
            except Exception as exc:
                logger().error(
                    "Failed to parse response for splunk access token",
                    exc_info=exc,
                )
                raise SplunkAccessTokenError("Unable to parse splunk access response")

            return SecretStr(json_response["access_token"])

    @tracer.start_as_current_span("_authenticate")
    def _authenticate(self) -> Service:
        token_string = self._get_token_string()
        svc: Service = splunklib.client.connect(
            scheme=self._protocol,
            host=self._host,
            port=self._port,
            token=token_string,
            app=self._app,
            autologin=True,
            retries=3,
            verify=self._ssl_verification,
            context=self._context if self._context else None,
        )

        def wrap(url, req):
            u = urlparse(url)

            if self._uri_add_prefix:
                path = os.path.join(self._uri_add_prefix, u.path.removeprefix("/"))
                u = u._replace(path=path)

            if req.get("headers"):
                req["headers"] = change_authorization_token_type("Splunk", "Bearer", req.get("headers"))

            resp = handler(verify=self._context is not None, context=self._context, timeout=300)(u.geturl(), req)

            return resp

        if self._uri_add_prefix is not None or self._context is not None:
            svc.http.handler = wrap

        return svc

    def _get_token_string(self) -> str:
        token_string = self._token.get_secret_value() if self._token else ""
        # If we are not provided a token we assume we should retrieve one through oauth client credentials flow
        if not self._token and self._token_oauth_hostname:
            ot = self.get_token_from_oauth()
            token_string = ot.get_secret_value() if ot else ""
        return token_string

    @staticmethod
    @tracer.start_as_current_span("retry_splunk_auth_error")
    def retry_splunk_auth_error(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            try:
                if self._client is None:
                    self._client = self._authenticate()

                return method(self, *args, **kwargs)
            except splunklib.binding.AuthenticationError:
                logger().warning("Authentication error with splunk, reconnecting and retrying request")
                self._client = self._authenticate()
                return method(self, *args, **kwargs)

        return wrapper

    @retry_splunk_auth_error
    def check_connection(self) -> bool:
        try:
            # perform lightweight call to verify connection
            return bool(self._client.info)
        except Exception as exc:
            logger().error("Error checking splunk connection", exc_info=exc)
            return False

    check_connection_async = async_wrap(check_connection)

    @retry_splunk_auth_error
    async def indexes(self) -> list[str]:
        # this returns only the indexes the user has access to
        # https://community.splunk.com/t5/Splunk-Search/Is-it-possible-to-get-a-list-of-available-indices/m-p/58945
        # including index=_* includes internal indexes as well
        indexes = await self.spl_query(
            "| eventcount summarize=false index=* index=_* | dedup index | fields index",
            earliest=None,
            latest=None,
            limit=-1,
        )
        return [i.get("index") for i in indexes]  # type: ignore[attr-defined]

    @retry_splunk_auth_error
    @tracer.start_as_current_span("get_uncached_fields_for_index")
    async def get_uncached_fields_for_index(self, index: str, lookback: str) -> list[SplunkField]:
        """
        Get fields for an index by querying the index directly. This is a fallback method if the dataset structure
        manager does not have the data for the index.
        """

        query = f"search index={index} | fieldsummary | table field values"
        result = await self.spl_query(query, lookback, "now", limit=-1)
        fields: list[SplunkField] = []
        for r in result:
            field = SplunkField(field_name=r["field"])
            values = json.loads(r["values"])
            if values and len(values) > 0 and "value" in values[0]:
                field.example_value = values[0]["value"]
                fields.append(field)

        return fields

    @retry_splunk_auth_error
    @tracer.start_as_current_span("get_fields_for_index")
    async def get_fields_for_index(self, index_name: str, lookback: str) -> list[SplunkField]:
        if index_name in self._field_cache:
            return self._field_cache[index_name]
        dataset_strucure = await DatasetStructureManager.instance().get_dataset_structure_async("splunk", index_name)
        if dataset_strucure:
            logger().debug("Using datset structure manager data for index %s", index_name)
            fields: list[SplunkField] = []
            for field in dataset_strucure.attributes:
                try:
                    fields.append(SplunkField.model_validate(field))
                except ValidationError:
                    return fields

            self._field_cache[index_name] = fields
            return fields
        else:
            logger().debug(
                "Datset structure manager data for index %s not found. Querying splunk directly.",
                index_name,
            )
            fields = await self.get_uncached_fields_for_index(index_name, lookback)
            self._field_cache[index_name] = fields
            return fields

    @retry_splunk_auth_error
    @tracer.start_as_current_span("_raw_spl_query_async")
    async def _raw_spl_query_async(
        self,
        spl: str,
        earliest: str | None = "-1h",
        latest: str | None = "now"
    ):
        if self._client is None:
            return [{"error": "Not connected to Splunk instance"}]

        kwargs = {
            "search_mode": "normal",
            "output_mode": "json",
            "count": 0,
        }

        if earliest:
            kwargs["earliest_time"] = f"{earliest}"

        if latest:
            kwargs["latest_time"] = f"{latest}"

        logger().info("Splunk query job to be issued: %s (from %s to %s)", spl, earliest, latest)

        def create_job(spl: str, **kwargs):
            return self._client.jobs.create(spl, **kwargs)

        job = await run_sync_in_executor(create_job, spl, **kwargs)
        stats = SplunkSearchStatus(sid=job.sid)
        start_time = datetime.now()
        sleep_time_seconds = 0.02
        max_sleep_time_seconds = 5
        consecutive_failures = 0
        max_consecutive_failures = 3
        while True:
            try:
                if not await run_sync_in_executor(job.is_ready):
                    await asyncio.sleep(sleep_time_seconds)
                    continue

                done = await run_sync_in_executor(job.is_done)  # storing in local var since job.is_done() is an API call
                stats.progress = float(job["doneProgress"]) * 100 if not done else 100
                stats.scan_count = int(job["scanCount"])
                stats.event_count = int(job["eventCount"])
                stats.result_count = int(job["resultCount"])
                stats.elapsed_seconds = (datetime.now() - start_time).total_seconds()

                logger().info(
                    "Splunk query %s %03.1f%%", stats.sid, stats.progress,
                    extra={"event_data": {
                        "spl": spl,
                        "earliest": earliest,
                        "latest": latest,
                        "stats": stats
                    }})

                if done:
                    break

                await asyncio.sleep(min(sleep_time_seconds, max_sleep_time_seconds))
                sleep_time_seconds *= 2
                consecutive_failures = 0
            except asyncio.exceptions.CancelledError:
                logger().info("Splunk query %s cancelled", stats.sid)
                with suppress(Exception):
                    await run_sync_in_executor(job.cancel)
                raise
            except Exception as ex:
                consecutive_failures += 1
                logger().error(
                    "Splunk search %s encountered consecutive error %d/%d while polling: %s",
                    stats.sid, consecutive_failures, max_consecutive_failures, ex)
                if consecutive_failures >= max_consecutive_failures:
                    with suppress(Exception):
                        await run_sync_in_executor(job.cancel)
                    raise

        if not await run_sync_in_executor(job.is_done):
            logger().error("Splunk job is not done, cannot extract results")
            raise Exception("Splunk job is not done, cannot extract results")
        response: list[dict[str, str]] = []
        # count=0 means return all results
        results = await run_sync_in_executor(job.results, output_mode='json', count=0)
        for result in splunklib_results.JSONResultsReader(results):
            if not isinstance(result, dict):
                continue  # results.Message type (diagnostic messages may be returned in results) or unexpected type

            response.append(result)
        return response

    @retry_splunk_auth_error
    @tracer.start_as_current_span("saved_searches")
    def saved_searches(
        self,
    ) -> list[SplunkSavedSearch]:
        key = md5(self._get_token_string().encode()).hexdigest()
        if key in saved_search_cache:
            logger().info("Using cache for Splunk saved searches")
            return saved_search_cache[key]

        saved_searches: list[SavedSearch] = self._client.saved_searches.list()
        saved_search_list: list[SplunkSavedSearch] = []
        for saved_search in saved_searches:
            saved_search_list.append(
                SplunkSavedSearch(
                    name=saved_search.name,
                    spl=saved_search["search"],
                )
            )
        saved_search_cache[key] = saved_search_list
        return saved_search_list

    saved_searches_async = async_wrap(saved_searches)

    @retry_splunk_auth_error
    @tracer.start_as_current_span("spl_query")
    async def spl_query(
        self,
        spl_query: str,
        earliest: str | None = "-1h",
        latest: str | None = "now",
        limit: int | None = 100
    ) -> list[dict[str, Any]]:
        spl_query = spl_query.strip()
        if not spl_query.startswith("|") and not spl_query.startswith("search"):
            spl_query = "search " + spl_query

        spl: str = spl_query.strip("'`\n\t\r ").replace("'", '"')

        if len(spl) == 0 or spl == "search":
            logger().warning(
                "Attempted to execute Splunk query with empty string. Returning empty results instead of executing."
            )
            return []

        if limit is None:
            limit = 100
        if limit > 0:
            spl += f" | head {limit}"

        return await self._raw_spl_query_async(spl, earliest, latest)

    async def execute_query(
        self, query: str, earliest: str | None = "-1h", latest: str | None = "now", limit: int | None = 100
    ) -> list[dict[str, Any]]:
        return await self.spl_query(
            spl_query=query, earliest=earliest, latest=latest, limit=limit
        )

    @retry_splunk_auth_error
    @tracer.start_as_current_span("create_notable_alert")
    async def create_notable_alert(
        self,
        tid: str,
        title: str,
        description: str,
        category: str,
        additional_fields: list[tuple[str, str]] | None = None,
    ) -> None:
        # TODO: splunk_es doesnt properly map these fields so alerts created here won't have proper priority
        query_fmt = '| makeresults count=1 | eval killchain="{title}", category="{category}", mitre_technique_description="{description}", annotations_mitre_attack="{tid}", _time=now()'
        if additional_fields and len(additional_fields) > 0:
            af = ", ".join(f'{first}="{second}"' for (first, second) in additional_fields)
            query_fmt += ", " + af

        query_fmt += " | collect index={index}"
        query_str = query_fmt.format(
            tid=tid,
            title=title.replace('"', '\"').replace("'", "\'"),
            category=category.replace('"', '\"').replace("'", "\'"),
            description=description.replace('"', '\"').replace("'", "\'"),
            index=self._notable_write_index,
        )

        logger().info("Creating notable alert: %s", query_str)
        await self._raw_spl_query_async(query_str)

    @retry_splunk_auth_error
    @tracer.start_as_current_span("delete_generated_notable_alerts")
    async def delete_generated_notable_alerts(
        self,
    ) -> None:
        await self._raw_spl_query_async(f"search index={self._notable_index} doc_id=* | delete", earliest="-24h")

    async def fetch_alerts(self, earliest: str, latest: str) -> list[dict[str, Union[str, list[str]]]]:
        start = datetime.now()
        alerts = await self.spl_query(
            f"search {self._get_notable_index()} | table* | eval andesite_time=_time",
            earliest,
            latest,
            limit=5000,
        )
        ConnectorMetrics.splunk_alerts_retrieval_latency.record((datetime.now() - start).total_seconds())
        return alerts

    async def fetch_alerts_by_ids(self, alert_ids: list[str]) -> list[dict[str, Union[str, list[str]]]]:
        notable_index = self._get_notable_index()
        alert_ids_formatted = ",".join(f'"{alert_id}"' for alert_id in alert_ids)
        alerts = await self.spl_query(
            f"{notable_index} | search event_id IN ({alert_ids_formatted}) | table* | eval andesite_time=_time",
            earliest=None,
            latest=None,
        )
        return alerts

    def _get_notable_index(self):
        return "`notable`" if self._es else f"index={self._notable_index} |  eval `get_event_id_meval`"
