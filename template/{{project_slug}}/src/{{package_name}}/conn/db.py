from {{package_name}}.settings import PostgresSettings
from sqlalchemy import create_engine
from sqlalchemy.sql import text


class Db:
    def __init__(self, config: PostgresSettings):
        self.config = config
        self.url = self.config.sqlalchemy_url
        self.engine = None
        self.connection = None

    def _create_sql(self, fields, model, domains=None):
        texto = "SELECT "
        if fields == []:
            texto += "*"
        else:
            for field in fields:
                texto += field
                if field != fields[-1]:
                    texto += ", "
        texto += " FROM " + model
        params = {}
        if domains:
            texto += " WHERE "
            for domain in domains:
                if domain[2]:
                    texto += domain[0] + " " + domain[1] + " :" + domain[0]
                    params[domain[0]] = domain[2]
                else:
                    texto += domain[0] + " " + domain[1]
                if domain[0] != domains[-1][0]:
                    texto += " AND "
        if "id" in fields:
            texto += " ORDER BY id ASC"
        return text(texto), params

    def _connect(self):
        if not self.engine:
            self.engine = create_engine(
                self.url,
                **self.config.engine_kwargs,
            )
        if not self.connection:
            self.connection = self.engine.connect()

    def search(self, fields, model, domain):
        sql, params = self._create_sql(fields, model, domain)
        return self.read_sql(sql, params)

    def read_sql(self, SQL, parametros=None):
        self._connect()
        import pandas as pd
        return pd.read_sql(SQL, params=parametros, con=self.engine)

    def get_conn(self):
        self._connect()
        return self.engine

    def exec_string(self, sql):
        self.exec(text(sql))

    def exec(self, sql):
        self._connect()
        self.connection.execute(sql)
        self.connection.commit()

    # def _get_sql(self, name):
    #     from epaodoo import env

    #     template = env.get_template(name)
    #     return text(template.render())
