import json
import httpx
import time
import random
from datetime import datetime
import sqlite3
import config as cfg
from dblib import db
from datetime import datetime


class har:
    def __init__(self, session=None, threadname=None, iteration=None,
                 pagename=None, hardata=None, excludedurls=None,
                 authurls=None, token=None):
        self.session = session
        self.threadname = threadname
        self.iteration=iteration
        self.pagename = pagename
        self.hardata = hardata
        self.excludedurls = excludedurls
        self.authurls = authurls
        self.token = token
        self.perf_db = db()


    def run(self):
        error_flags = []
        resp_times = [0]
        resp_codes = []

        objects = self.hardata.get("log", {}).get("entries", [])

        for obj in objects:
            error_flag = ""
            reqobj = obj.get("request", {})

            url = reqobj.get("url", "")
            method = reqobj.get("method", "").upper()

            # Exclude URLs
            if url.startswith(tuple(self.excludedurls)) or url.endswith(tuple(self.excludedurls)):
                continue

            # -----------------------------
            # Build Query Parameters
            # -----------------------------
            querystring = reqobj.get("queryString", [])
            params = {}

            for q in querystring:
                params[q.get("name", "")] = q.get("value", "")

            if not params:
                params = None

            # -----------------------------
            # Build Request Headers
            # -----------------------------
            headers = reqobj.get("headers", [])
            reqheaders = {}

            ignored_headers = [
                "content-length",
                "host",
                "connection",
                "transfer-encoding",
                "accept-encoding",
                "cookie"
            ]

            for header in headers:

                name = header.get("name", "")

                if not name:
                    continue

                if name.startswith(":"):
                    continue

                if name.lower() in ignored_headers:
                    continue

                reqheaders[name] = header.get("value", "")

            # -----------------------------
            # Add Authorization Token
            # -----------------------------
            if url.startswith(tuple(self.authurls)) or url.endswith(tuple(self.authurls)):
                reqheaders["Authorization"] = f"Bearer {self.token}"

            # -----------------------------
            # Get Body
            # -----------------------------
            postdata = reqobj.get("postData", None)
            body = None

            if postdata:
                body = postdata.get("text", "")

            # -----------------------------
            # Execute Request
            # -----------------------------

            # get start time
            start_time = datetime.now()
            start_time_pc = time.perf_counter()

            resp = None
            error_flag = ""

            try:

                if method == "GET":

                    resp = self.session.get(
                        url=url,
                        headers=reqheaders,
                        params=params
                    )


                elif method == "POST":

                    resp = self.session.post(
                        url=url,
                        headers=reqheaders,
                        params=params,
                        content=body
                    )


                elif method == "PUT":

                    resp = self.session.put(
                        url=url,
                        headers=reqheaders,
                        params=params,
                        content=body
                    )


                elif method == "DELETE":

                    resp = self.session.delete(
                        url=url,
                        headers=reqheaders,
                        params=params,
                        content=body
                    )


                elif method == "OPTIONS":

                    resp = self.session.options(
                        url=url,
                        headers=reqheaders,
                        params=params
                    )

                else:
                    continue

            except Exception as ex:
                pass

            if resp:
                status_code = resp.status_code
                resp_codes.append(resp.status_code)

            # get end time
            end_time = datetime.now()
            end_time_pc = time.perf_counter()

            # calculate response time in sec
            response_time = (end_time_pc - start_time_pc) * 1000
            resp_times.append(response_time)

            if status_code in cfg.valid_status_codes:
                error_flag = "P"
            elif status_code in cfg.ignore_status_codes:
                error_flag = "W"
            else:
                error_flag = "F"

            error_flags.append(error_flag)

            try:
                resp_content = json.dumps(resp.json(), indent=4)
                resp_type = "json"
            except ValueError:
                resp_content = resp.text
                resp_type = "text"

            try:
                req_headers = json.dumps(dict(resp.request.headers), indent=4)
            except:
                req_headers = ""

            self.perf_db.log_performance(self.pagename, self.threadname, self.iteration,
                                         start_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
                                         end_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
                                         cfg.samples_started,
                                         cfg.samples_completed,
                                         cfg.running_users,
                                         0,
                                         response_time,
                                         error_flag,
                                         cfg.error_percent,
                                         status_code,
                                         resp_type,
                                         resp_content,
                                         url,
                                         method,
                                         json.dumps(req_headers))

        return error_flags, max(resp_times), max(resp_codes)

    @task(name='testpage123', weight=2, type='har', enabled=True)
    def tdsr1(self, user_session, tname, iteration):

        excludeurls=["sample/auth"]
        authurl=['sample/getwithauth']
        token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6Imp2QGpvc2VwaHZhcmdoZXNlLmNhIiwiaWF0IjoxNzg0ODU3NDYxLCJleHAiOjE3ODQ4NjEwNjF9.fSi5gfml7CAaHYIQsnF-8AJR2iz2c1JKoex-T1Q5pJI"

        h=har(session=user_session, threadname=tname, iteration=iteration,
        pagename="testpage", hardata=hd.h, excludedurls=excludeurls,
        authurls=authurl, token=token)
        error_flags, resp_time, resp_code = h.run()
        return self.tdsr1.test_name, error_flags, resp_time, resp_code