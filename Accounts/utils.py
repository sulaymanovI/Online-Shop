import requests

channel_id = ''
bot_token = ''


def send_ms_to_channel(code):
    link = f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={channel_id}%text=Verification code : {code}'
    requests.get(link)

    return code