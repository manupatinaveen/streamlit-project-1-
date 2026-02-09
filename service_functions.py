import requests
import json
import logging
import streamlit as st


def make_service_request(service_name, req_headers, payload, payload_type,inline_param={},method="POST",rise_error_on_204=True):
    from config import SchApp,logger
    connection_url = SchApp.config()["services"]['url']
    logging.info("Config file: Loaded connection URL " + connection_url)

    service_url = str(connection_url) + SchApp.config()["services"][service_name]
    logging.info("Service url"+service_url)
    if len(inline_param) != 0:
        for i in inline_param:
            if str(i) in service_url:service_url=service_url.replace(str(i),str(inline_param[i]))
    try:
        if payload_type == "json":
            logging.info("Service URL " + str(service_url) + " Payload " + str(payload) + " Headers " + str(req_headers))
            response_json = requests.request("POST", url=service_url, json=payload, headers=req_headers)
            print("service_url",service_url)
            print("payload",payload)
            if response_json.status_code == 200:
                service_resp = json.loads(response_json.text)
                return service_resp
            elif response_json.status_code == 204:
                logging.info(" Service URL: " + str(service_url) + " Status: " + str(
                    response_json.status_code) + " Reason: " + str(response_json.reason))
                return []
            elif rise_error_on_204==False:
                logging.info(" Service URL: " + str(service_url) + " Status: " + str(
                    response_json.status_code) + " Reason: " + str(response_json.reason))
                return []
            else:
                logging.info(" Service URL: " + str(service_url) + " Status: " + str(response_json.status_code) + " Reason: " + str(response_json.reason))
                raise Exception("Service call :" + response_json.reason, response_json.status_code)
        else:
            if payload_type != "get_json":
                if payload is not None:
                    if len(payload) != 0:
                        param_adjunt = '?'
                        for i, j in payload.items():
                            param_adjunt += f"{i}={j}&"
                        param_adjunt = param_adjunt[:-1]
                    service_url = str(service_url) + str(param_adjunt)
                if payload_type == "query_params":
                    payload=None
            else:
                pass
            logging.info("Service URL " + str(service_url) + " Payload " + str(payload) + " Headers " + str(req_headers) + " query_params")
            response_json = requests.request(method, url=service_url, json=payload, headers=req_headers)
            if response_json.status_code == 200:
                service_resp = json.loads(response_json.text)
                return service_resp
            elif response_json.status_code == 204:
                logging.info(" Service URL: " + str(service_url) + " Status: " + str(
                    response_json.status_code) + " Reason: " + str(response_json.reason))
                return []
            else:
                logging.info(" Service URL: " + str(service_url) + " Status: " + str(
                    response_json.status_code) + " Reason: " + str(response_json.reason))
                return []
    except Exception as e:
        logger.exception(e, stack_info=True)
        raise e