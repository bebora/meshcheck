# meshcheck
Meshcheck is a simple Python 3 script that monitors available mesh bags colors from zcube.vip.  
A basic Telegram bot will notify changes to users specified in tokens.json  

tokens.json should be structured as follows:
```
{
  "users_id": [
    "telegram_chat_id"
  ],
  "bot_token": "telegram_bot_token"
}
```
