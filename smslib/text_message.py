from datetime import datetime, timezone
import requests
from mysql.connector.cursor import CursorBase
from mysql.connector.connection import MySQLConnection
import os
import json


def send(client: str, to: str, message: str, sql_connection: MySQLConnection):
    '''
    Send a text message using SMSAPI/Link Mobility by default or fallback on Mailjet API
    '''
    now = datetime.now(timezone.utc)
    rangeStart = now.replace(
        day=1, hour=0, minute=0, second=0).strftime('%Y-%m-%d %H:%M:%S')
    rangeEnd = now.strftime('%Y-%m-%d %H:%M:%S')

    cur: CursorBase = sql_connection.cursor(dictionary=True)
    query = 'SELECT COUNT(id) AS sms_current FROM `boardonh_onboarding_{}`.log WHERE event_type = %s AND timestamp >= %s AND timestamp <= %s'.format(
        client)
    cur.execute(query, ('received_sms', rangeStart, rangeEnd))
    resultCurrent = cur.fetchone()['sms_current']

    query = 'SELECT sms_count FROM `boardonh_onboarding_{}`.client_view WHERE 1 LIMIT 1'.format(
        client)
    cur.execute(query)
    resultMax = cur.fetchone()['sms_count']
    if resultCurrent > resultMax:
        raise Exception("SMS quota exceeded ({}/{})".format(resultCurrent, resultMax))

    cur.execute('SELECT sms_from FROM `boardonh_onboarding_{}`.config WHERE %s LIMIT 1'.format(
        client), (1,))
    rs = cur.fetchone()
    sms_from = rs['sms_from'][0:11]

    try:
        sms_id = __send_smsapi(message, to, sms_from)
    except Exception:
        sms_id = __send_mailjet(message, to, sms_from)

    cur.execute(
        "INSERT INTO boardonh_onboarding.sms_log (sms_id, client) VALUES (%s, %s)", (sms_id, client))
    sql_connection.commit()
    cur.close()

    return sms_id


def __send_smsapi(message, phone, sms_from):
    response = requests.post('https://api.smsapi.se/sms.do', data=json.dumps({
        'from': sms_from,
        'to': phone.replace('+', ''),
        'message': message,
        'format': 'json'
    }), headers={
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(os.environ['BOARDON_SMSAPI_TOKEN'])
    })

    data = response.json()
    if response.status_code > 299:
        raise Exception(response.text)
    elif 'error' in data:
        raise Exception(data['message'])

    return data['list'][0]['id']


def __send_mailjet(message, sms_to, sms_from):
    token = os.environ['BOARDON_MAILJET_SMS_TOKEN']
    url = 'https://api.mailjet.com/v4/sms-send'
    response = requests.post(url, data=json.dumps({
        'From': sms_from,
        'To': sms_to,
        'Text': message
    }), headers={
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(token)
    })
    data = response.json()
    if response.status_code != 200 or 'ErrorCode' in data:
        raise Exception(data)

    return data['ID']
