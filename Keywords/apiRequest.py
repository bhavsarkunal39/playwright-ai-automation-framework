import requests
import logging
from Keywords.exceptionLog import ExceptionLog

class APIrequest:
   
    @staticmethod
    def read_request(path):
        
        logging.info(f"Reading request body: {path}")
        try:
            with open(f"{path}", "r") as file:
                body = file.read()
        except Exception as e:
            ExceptionLog.exceptionLog(e,"read_request()",path)
        return body
    
    @staticmethod
    def api_get(url,token=None,data=None,headers=None):
        logging.info(f"Running get() API.")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
            }
        try:
            response= requests.get(url,data=data,headers=headers,verify=False)
            logging.info(f"API Response: {response.json()}")
            return response
        except Exception as e:
            ExceptionLog.exceptionLog(e,"api_get()",url)
    
    
    @staticmethod
    def api_post(url,data=None,token=None,headers=None):
        logging.info(f"Running post() API.")
        if headers is None:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
                }
        try:
            response=requests.post(f"{url}",data=data,headers=headers,verify=False)
            #logging.info(f"API Response: {response.json()}")
            return response
        except Exception as e:
            ExceptionLog.exceptionLog(e,"api_post()",response.text)
    
    
    @staticmethod
    def api_put(url,data=None,token=None,headers=None):
        logging.info(f"Running put() API.")
        if headers is None:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
                }
        try:
            response= requests.put(f"{url}",data=data,headers=headers,verify=False)
            logging.info(f"API Response: {response.json()}")
            return response
        except Exception as e:
            ExceptionLog.exceptionLog(e,"api_put()",url)
    
    
    @staticmethod
    def api_delete(url,token=None,headers=None):
        logging.info(f"Running delete() API.")
        if headers is None:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
                }
        try:
            response= requests.delete(f"{url}",headers=headers,verify=False)
            logging.info(f"API Response: {response.json()}")
            return response
        except Exception as e:
            ExceptionLog.exceptionLog(e,"api_delete()",url)