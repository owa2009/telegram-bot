import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
import threading
import asyncio
import alertsLoop
from os.path import exists

# Constants
API_KEY = "https://api.binance.com/api/v3/ticker/price?symbol="
FILENAME = "data/data.txt"
TELEGRAM_TOKEN = "6771564107:AAG2MHvb2e0W6-pVreOhdIXRAJTRMOdcCss"
CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"

# Global variable to store the AlertsLoop instance
alert_loop_instance = None
usersLooping = []
loop_thread = None
start_msg = "Hi I am an Alerting Bot developped by @wailouk, these are some commands that you can use : \n /add (alert name) (Currency or Symbol) (price) - This command adds a new alert to the registry \n /loop - This command starts the looping functions to check if alerts have been triggered \n /stop - This command stops the looping functions \n /edit (old alert name) (new alert name) (Symbol) (price) - This command modifies the alert data \n /dlt (alert name) - This command deletes the alert \n /show - This command shows your active alerts \n Note: you can't add or edit or delete any alert while the looping function is running therfor, the command /stop exists ! \n !!! Enjoy using our free alerting bot !!!"

def addSymbol(symbol, alertName, price, fileName):
    if exists(fileName):
        with open(fileName, "a") as saveFile:
            saveFile.write(f"{alertName} : {symbol} = {price};")
    else:
        with open(fileName, "w") as saveFile:
            saveFile.write(f"{alertName} : {symbol} = {price};")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=start_msg)

async def show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    active_alerts = ""
    user = update.effective_chat.id
    FILENAME = "data/"+str(update.effective_chat.id)+".txt"
    with open(FILENAME, "r") as saveFile:
            data = saveFile.read()
    active_alerts = "Your active alerts are : \n"+str(data.replace(";","\n"))
    await context.bot.send_message(chat_id=update.effective_chat.id, text=active_alerts)

async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_chat.id
    msg = update.message.text
    FILENAME = "data/"+str(update.effective_chat.id)+".txt"
    msg_data = list(filter(None, msg.replace("/edit ", "").split(" ")))
    if not msg_data == None:
        old_alert_name = msg_data[0]
        alert_name = msg_data[1]
        symbol = msg_data[2]
        price = msg_data[3]
        row = f"{alert_name} : {symbol} = {price}"
        with open(FILENAME, "r+") as saveFile:
            data = saveFile.read()
            print(data)
            data = list(filter(None, data.split(";")))
        with open(FILENAME, "w") as saveFile:
            for x in data:
                name = x.split(" : ")[0]
                print(name)
                if old_alert_name == name:
                    old_alert = data.index(x)
                    print(data[old_alert])
                    data[old_alert] = row
                    break
            if len(data) == 1:
                data.append("")
            data = ";".join(data)
            saveFile.write(data)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Alert Modified Successfully")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Uncorrect command form, please enter the command in this form(without brackets) : \n /edit (old alert name) (new alert name) (Symbol) (price)")

async def dlt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_chat.id
    msg = update.message.text
    FILENAME = "data/"+str(update.effective_chat.id)+".txt"
    msg_data = list(filter(None, msg.replace("/dlt ", "").split(" ")))
    if not msg_data == None:
        alert_name = msg_data[0]
        with open(FILENAME, "r+") as saveFile:
            data = saveFile.read()
            data = list(filter(None, data.split(";")))
        with open(FILENAME, "w") as saveFile:
            for x in data:
                name = x.split(" : ")[0]
                if alert_name == name:
                    alert = data.index(x)
                    data.remove(data[alert])
                    break
            print(data)
            if len(data) == 1:
                data.append("")
            data = ";".join(data)
            saveFile.write(data)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Alert Deleted Successfully")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Uncorrect command form, please enter the command in this form(without brackets) : \n /dlt (alert name)")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    FILENAME = "data/"+str(update.effective_chat.id)+".txt"
    data = msg.replace("/add ", "").split(" ")
    log = False
    if not data == None:
        alert_name = data[0]
        symbol = data[1]
        price = data[2]
        if exists(FILENAME):
            with open(FILENAME, "r+") as saveFile:
                data = saveFile.read()
                print(data)
                data = list(filter(None, data.split(";")))
                for x in data:
                    name = x.split(" : ")[0]
                    if alert_name == name:
                        log = True
        if log == False:
            addSymbol(symbol, alert_name, price, FILENAME)
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Alert Added Successfully")
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="This Alert Name Already Exists, Please Change It With Unused one")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Uncorrect command form, please enter the command in this form(without brackets) : \n /add (alert name) (Symbol) (price)")

async def looping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global alert_loop_instance, loop_thread
    user = update.effective_chat.id
    if user not in usersLooping:
        usersLooping.append(user)
        FILENAME = "data/"+str(update.effective_chat.id)+".txt"
        alert_loop_instance = alertsLoop.AlertsLoop(FILENAME, API_KEY, TELEGRAM_TOKEN, update.effective_chat.id)
        loop_thread = threading.Thread(target=alert_loop_instance.start_loop)
        loop_thread.start()
        await context.bot.send_message(chat_id=update.effective_chat.id, text="I have started looping")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Looping is already running")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global alert_loop_instance, loop_thread
    user = update.effective_chat.id
    if user in usersLooping:
        usersLooping.remove(user)
        alert_loop_instance.stop_loop()
        loop_thread.join()
        alert_loop_instance = None
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Looping has been stopped")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="No looping is running")

if __name__ == '__main__':
    application = ApplicationBuilder().token('6771564107:AAG2MHvb2e0W6-pVreOhdIXRAJTRMOdcCss').build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    loop_handler = CommandHandler('loop', looping)
    application.add_handler(loop_handler)

    add_handler = CommandHandler('add', add)
    application.add_handler(add_handler)

    show_handler = CommandHandler('show', show)
    application.add_handler(show_handler)

    edit_handler = CommandHandler('edit', edit)
    application.add_handler(edit_handler)

    dlt_handler = CommandHandler('dlt', dlt)
    application.add_handler(dlt_handler)

    stop_handler = CommandHandler('stop', stop)
    application.add_handler(stop_handler)

    application.run_polling()
