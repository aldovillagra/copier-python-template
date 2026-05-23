import json
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from {{package_name}}.settings import OdooSettings
import pandas as pd


class Odoo:
    def __init__(self, config: OdooSettings):
        self.config = config
        self.url = self.config.host + ":" + str(self.config.port)
        self.db = self.config.db
        self.username = self.config.username
        self.password = self.config.password.get_secret_value()
        self.lang = self.config.lang
        self.uid = None
        self.uid_rpc = None

        # JSON-RPC config
        self._jsonrpc_url = self.url.rstrip("/") + "/jsonrpc"
        self._timeout = 60  # seconds
        self._retries = 2
        self._retry_sleep = 0.8

        # Default context; you can extend via config if needed
        extra_ctx = {}
        self._context = {"lang": self.lang, **extra_ctx}

    def version(self):
        return self._call_service("common", "version")

    def check_uid(self):
        self._connect()
        return bool(self.uid)

    def _connect(self):
        if self.uid_rpc is None:
            self.uid_rpc = self._call_service(
                "common", "login", self.db, self.username, self.password
            )
        # unify uid
        self.uid = self.uid_rpc

    # -----------------------
    # JSON-RPC core
    # -----------------------
    def _json_rpc(self, url: str, method: str, params: dict) -> Any:
        """
        Low-level JSON-RPC request with retry/timeout and normalized errors.
        """
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": random.randint(0, 1000000000),
        }
        data = json.dumps(payload).encode("utf-8")
        req = Request(
            url=url,
            data=data,
            headers={"Content-Type": "application/json"},
        )

        last_err = None
        for attempt in range(self._retries + 1):
            try:
                with urlopen(req, timeout=self._timeout) as resp:
                    raw = resp.read().decode("utf-8")
                reply = json.loads(raw)
                if reply.get("error"):
                    raise RuntimeError(self._format_jsonrpc_error(reply["error"]))
                return reply["result"]
            except (HTTPError, URLError, TimeoutError, ValueError, RuntimeError) as e:
                last_err = e
                if attempt < self._retries:
                    time.sleep(self._retry_sleep * (attempt + 1))
                    continue
                raise
        # should not happen
        raise last_err

    def _format_jsonrpc_error(self, err: dict) -> str:
        """
        Odoo JSON-RPC error usually has: code, message, data {name, debug, arguments}
        """
        if not isinstance(err, dict):
            return str(err)
        msg = err.get("message") or "JSON-RPC error"
        data = err.get("data") or {}
        name = data.get("name")
        debug = data.get("debug")
        args = data.get("arguments")
        parts = [msg]
        if name:
            parts.append(f"name={name}")
        if args:
            parts.append(f"arguments={args}")
        # debug puede ser enorme; normalmente conviene loguearlo, no lanzarlo entero
        if debug:
            parts.append("debug=<omitted>")
        return " | ".join(parts)

    def _call_service(self, service: str, method: str, *args) -> Any:
        return self._json_rpc(
            self._jsonrpc_url,
            "call",
            {"service": service, "method": method, "args": list(args)},
        )

    def execute_kw(
        self,
        model: str,
        method: str,
        args: Optional[list] = None,
        kwargs: Optional[dict] = None,
    ) -> Any:
        """
        JSON-RPC equivalent to xmlrpc/2/object execute_kw.
        """
        self._connect()
        args = args or []
        kwargs = kwargs or {}

        # Ensure context is always applied unless overridden
        ctx = kwargs.get("context")
        if ctx is None:
            kwargs["context"] = dict(self._context)
        else:
            merged = dict(self._context)
            merged.update(ctx)
            kwargs["context"] = merged

        return self._call_service(
            "object",
            "execute_kw",
            self.db,
            self.uid_rpc,
            self.password,
            model,
            method,
            args,
            kwargs,
        )

    def search(self, fields, model, domain) -> pd.DataFrame:
        resultado = self.execute_kw(
            model,
            "search_read",
            args=[domain],
            kwargs={"fields": fields},
        )
        return pd.DataFrame.from_records(resultado)

    def search_read_paged(
        self,
        model: str,
        domain: list,
        fields: list[str],
        batch: int = 200,
        order: str = "id",
    ):
        """
        Generador que devuelve páginas de resultados (list[dict]) vía search_read con limit/offset.
        """
        offset = 0
        while True:
            res = self.execute_kw(
                model,
                "search_read",
                args=[domain],
                kwargs={
                    "fields": fields,
                    "limit": batch,
                    "offset": offset,
                    "order": order,
                },
            )
            if not res:
                break
            yield res
            offset += batch

    def fields_get(self, model):
        return self.execute_kw(
            model,
            "fields_get",
            args=[],
            kwargs={
                "attributes": [
                    "string",
                    "help",
                    "type",
                    "relation",
                    "readonly",
                    "required",
                    "store",
                    "related",
                ]
            },
        )

    def create(self, model, datos):
        # datos: dict
        return self.execute_kw(model, "create", args=[datos])

    def create_all(self, model, datos):
        # datos: List[dict] (batch create). Odoo expects args=[list_of_dicts]
        return self.execute_kw(model, "create", args=[datos])

    # Nuevas variantes (no rompen las existentes)
    def create_ctx(self, model, datos, context=None):
        return self.execute_kw(
            model, "create", args=[datos], kwargs={"context": context or {}}
        )

    def create_all_ctx(self, model, datos, context=None):
        return self.execute_kw(
            model, "create", args=[datos], kwargs={"context": context or {}}
        )

    def write(self, id, model, datos):
        # keep signature: write(id, model, datos) but supports id=int or list[int]
        ids = id if isinstance(id, list) else [id]
        return self.execute_kw(model, "write", args=[ids, datos])

    def exec(self, model, function_name, datos):
        # Keep compatibility with your old "exec" contract: [datos] as positional args.
        # If you sometimes passed already-a-list, this will change behavior; see note below.
        return self.execute_kw(model, function_name, args=[datos])

    def call_rpc(self, model, function, datos):
        """
        Backward-compatible helper. Prefer execute_kw().
        Your old call_rpc used "execute" not "execute_kw"; keep same behavior if needed.
        """
        self._connect()
        return self._call_service(
            "object",
            "execute",
            self.db,
            self.uid_rpc,
            self.password,
            model,
            function,
            datos,
        )
