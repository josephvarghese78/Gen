import json
import httpx
import time
har_data=None

token="eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6ImFGa21LVkZjLTRXVjZzWENCdk5aa1hJNTA1WSJ9.eyJhdWQiOiI2ZjY2Y2YyYy1jMWI0LTQ3MmMtOWUzZi1jNmRmNWFkN2Y0ODEiLCJpc3MiOiJodHRwczovL2xvZ2luLm1pY3Jvc29mdG9ubGluZS5jb20vNWQzZTI3NzMtZTA3Zi00NDMyLWE2MzAtMWEwZjY4YTI4YTA1L3YyLjAiLCJpYXQiOjE3ODM1Mjk3NTUsIm5iZiI6MTc4MzUyOTc1NSwiZXhwIjoxNzgzNTM0MzY3LCJhaW8iOiJBY1FBTy84Y0FBQUFvZHhTbCtHL3B4a2RaU003UHk3N2Y0SXlCSDBBaFRiS0ZZaGoyT1BNNFE4UjdKWnhFRVRvVXRkRXVmZlhpS1owcWI4MFNyVXhPaG1BRzVMSG5zU1V5VGk3eVZEcHRjbkVhWXpQblVUN3VWYjRJSFQwbWxvV05TT1Q3V0xEbFp5Y3hJZlVCNm15b3NuRU03SThHSU5SQ0pvMTBZbk9PSWFoeWpZZzZnSklIbEtEWGVvRG9JV3Y1UlJrL1E5OFVsUERkZFduMVp0M2E1MXF3TTVXQmRkamkxOW91b1YwUFJaaFRqbFRyb3Z6V1FuNzhiUXVMYnI1c254bEFwZDdJUjJjIiwiYXpwIjoiM2ZhN2FiYWItZWQwZC00ZDA1LWFjNzctYzRmMzYwODllMGUyIiwiYXpwYWNyIjoiMSIsIm5hbWUiOiJKb3NlcGggVmFyZ2hlc2UiLCJvaWQiOiJkYWM4MGJlNS02NzQxLTRjZjYtODViYS03ZDY5MjE2YTUyMzEiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJ2YXJnaGpvQE1GQ0dELkNPTSIsInJoIjoiMS5BUk1BY3ljLVhYX2dNa1NtTUJvUGFLS0tCU3pQWm0tMHdTeEhual9HMzFyWDlJRVRBUG9UQUEuIiwicm9sZXMiOlsiY29udHJpYnV0b3JzIiwiYnJpZGdla2VlcGVyOm1vZGVsOmdwdC01LW5hbm8iLCJicmlkZ2VrZWVwZXI6dXNlciJdLCJzY3AiOiJ1c2VyX2ltcGVyc29uYXRpb24iLCJzaWQiOiIwMDVlZjBjYS04ODIyLTVlMWItZjU5OC1iYThhYWJjYTA1ZTUiLCJzdWIiOiJjRW55Q1Fjb1gtNWpnRjl4cGJkSEk2b051Z09vbDgwakVRc2ZJeHdWVFV3IiwidGlkIjoiNWQzZTI3NzMtZTA3Zi00NDMyLWE2MzAtMWEwZjY4YTI4YTA1IiwidXRpIjoiNmQtNGJzT19NMDJVVV8zdjdsaGtBQSIsInZlciI6IjIuMCIsInhtc19mdGQiOiJYSlhFOTd5SHhtZXlKOXBURTFWQXl1WHZ1VEMtWWg1cTlRenJ3TGUzdWNjQmRYTjNaWE4wTXkxa2MyMXoifQ.iBF8Ldl2e9eQlnR6EJlruxb61dHD8xfXogLOamZvXUUR5arIQb1ci2qs5CNVAd3zXWFy2N7QbkkrIxbnCOxP6UZtIQIMmj5dKuZPbjpMrPNGiyA4VCN5rRxYMFu4bLD_907oZEcWTcEGxLByaZXg0rmvPcY7zfeTSB1zNcZMvZd1rJywRunnAJ02l2QxW8JXoGZud09_pB0Dgv206chvuLpBUb7rdEE-LAnEsMv6xr5CyussRTGKwDOcHkzIhpfuS5uve1uYFffEov4WNAaCjeCgyo_qh3dQxldpQMhUeUQbALO8D89YdgEfiHzpT1qXEMJpbUfWI7KnJk7pvQujVw"

def get_pageresponse(url, method, headers):
    start_time=time.time()
    with httpx.Client(http2=True) as client:
        headers["Authorization"]=f"Bearer {token}"
        if method=="GET":
            resp = client.get(f'{url}', headers=headers)
        elif method=="POST":
            resp = client.post(f'{url}', headers=headers)
        elif method=="PUT":
            resp = client.put(f'{url}', headers=headers)
        elif method=="DELETE":
            resp = client.delete(f'{url}', headers=headers)
        elif method=="OPTIONS":
            resp = client.options(f'{url}', headers=headers)
        else:
            return None
    end_time=time.time()
    #elapsed_time=end_time-start_time
    elapsed_time = resp.elapsed.total_seconds()*1000
    resp_code=resp.status_code
    return resp, resp_code, elapsed_time

def process_har(harfile):
    with open('./projects.json', 'r') as f:
        har_data = json.load(f)

    objects=har_data.get("log", {}).get("entries",[1])
    elapsed_times=[]

    for obj in objects:
        reqobj=obj.get("request", {})
        url = reqobj.get("url", "")
        if url.startswith("https://webapp-fe-gaip-use2-create-ai-platform-uat.azurewebsites.net"):
            respheaders=obj.get("response", {}).get("headers", {})
            content_type=next((header["value"] for header in respheaders if header.get("name", "").lower() == "content-type"), "")
            reqheader={}
            method=reqobj.get("method", "")
            headers=reqobj.get("headers", [])
            for header in headers:
                if not header.get("name", "").startswith(":"):
                    reqheader[header.get("name", "")]=header.get("value", "")

            print("="*50)
            print(f"Method: {method}")
            print(f"URL: {url}")
            print(f"Headers: {json.dumps(reqheader, indent=4)}")
            print("Content-Type:", content_type)
            resp, resp_code, elapsed_time=get_pageresponse(url, method, reqheader)
            #print("Response:", resp.text)
            elapsed_times.append(elapsed_time)
            print("Code:", resp_code)
            print("Elapsed Time:", elapsed_time)
            print("=" * 50)
            print("")

    return harfile, elapsed_times[0] + max(elapsed_times) + 1 if elapsed_times else 0


f=process_har("")
print(f)