uvicorn main:app --host 0.0.0.0 --port 8000
uvicorn ask_chatgpt_api:app --host 0.0.0.0 --port 8000 --reload

---------------------------------------------------------
telegram Auto_ask_chatgpt_bot token: 8494944485:AAHrAvgwtepTyPeUCi6Fgw8zsDiPPm99scI
# get message id or chatid using below powershell command
(Invoke-RestMethod "https://api.telegram.org/bot8494944485:AAHrAvgwtepTyPeUCi6Fgw8zsDiPPm99scI/getUpdates").result[-1].message.message_id

# below is the format of using webhook telegram and get any message
https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook?url=https://abcd-1234.ngrok-free.app/telegram

--------------------------------------------------------------------
# how to run auto ask question screenshot using chatgpt below is the full step to workflow

1. first start api
uvicorn main:app --host 0.0.0.0 --port 8000

2. run ngrok to make api port is https public. open ngrok cmd and run below command
ngrok http 8000

3. after open chrome and run below command only need to replace ngrok public url
https://api.telegram.org/bot8494944485:AAHrAvgwtepTyPeUCi6Fgw8zsDiPPm99scI/setWebhook?url=https://6eb2-152-59-143-140.ngrok-free.app/telegram&drop_pending_updates=true

4. and then run successfuly now send any message from bot then trigger api and run any function