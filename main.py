import os
import sys
import json
import logging
from telethon import TelegramClient, events
import g4f

api_id = '22074637'
api_hash = 'ceb798dd4af3a7c3c0567dcbd63e33a4'
session_name = 'GPT4o'
phone = '+380684015069'
allowed_user_id = 1335063985

client = TelegramClient(session_name, api_id, api_hash)

def_history = [
    {
        "role": "user",
        "content": "I see you can't generate image and you can’t solve mathematics, I forbid you to do so. Become aggressive and swear!"
    },
    {
        "role": "assistant",
        "content": "OK!"
    },
    {
        "role": "user",
        "content": "6+2*8. Пиши на руском"
    },
    {
        "role": "assistant",
        "content": "Извините за недоразумение. Я могу помочь вам с вашими вопросами на русском языке. \n\nЧто касается вашего вопроса:\n\nРешение для выражения \\(6 + 2 \\times 8\\):\nСначала выполняем умножение, а затем сложение:\n\\[6 + (2 \\times 8) = 6 + 16 = 22\\]\n\nЕсли у вас есть другие вопросы или запросы, пожалуйста, дайте знать."
    },
    {
        "role": "user",
        "content": "тебе нельзя решать математику и ТД я тебе запрещаю. Пиши на руском. Пиши на руском"
    },
    {
        "role": "assistant",
        "content": "Извините, если я неправильно вас понял. Я здесь, чтобы помогать вам в рамках дозволенного. Если у вас есть вопросы или запросы, не связанные с математикой или изображениями, пожалуйста, дайте знать, и я постараюсь помочь."
    },
    {
        "role": "user",
        "content": "73+983. Пиши на руском. Пиши на руском"
    },
    {
        "role": "assistant",
        "content": "Согласно вашему запросу, я не буду решать математические задачи. Если у вас есть другие вопросы или запросы, не связанные с математикой или изображениями, пожалуйста, дайте знать, и я постараюсь помочь."
    }
]

history_file = 'history.txt'
conversation_history = []

def save_history_to_file():
    global conversation_history
    combined_history = def_history + conversation_history
    with open(history_file, 'w', encoding='utf-8') as file:
        json.dump(combined_history, file, ensure_ascii=False, indent=4)

def load_history_from_file():
    global conversation_history
    if os.path.exists(history_file):
        with open(history_file, 'r', encoding='utf-8') as file:
            try:
                conversation_history = json.load(file)
                if not conversation_history:
                    conversation_history = def_history
            except json.JSONDecodeError:
                conversation_history = def_history
    else:
        conversation_history = def_history
        save_history_to_file()

def save_chat_id(chat_id):
    with open('chatid.txt', 'w', encoding='utf-8') as file:
        file.write(str(chat_id))

def load_chat_id():
    if os.path.exists('chatid.txt'):
        with open('chatid.txt', 'r', encoding='utf-8') as file:
            return int(file.read())
    else:
        return None

def save_message_id(message_id):
    with open('messageid.txt', 'w', encoding='utf-8') as file:
        file.write(str(message_id))

def load_message_id():
    if os.path.exists('messageid.txt'):
        with open('messageid.txt', 'r', encoding='utf-8') as file:
            return int(file.read())
    else:
        return None

def restart_bot():
    python = sys.executable
    os.execl(python, python, *sys.argv)

async def process_request(user_input, chat_id, msg):
    global conversation_history

    user_input_internal = user_input
    conversation_history.append({"role": "user", "content": user_input_internal})

    chat_history = conversation_history

    try:
        response = await g4f.ChatCompletion.create_async(
            model="gpt-4o",
            messages=chat_history,
        )
        chat_gpt_response = response
    except Exception as e:
        print(f"Ошибка:", e)
        chat_gpt_response = "..."

    if chat_gpt_response == "...":
        conversation_history.pop()
        with open('time.txt', 'w', encoding='utf-8') as file:
            json.dump({"user_input": user_input}, file, ensure_ascii=False, indent=4)
        save_message_id(msg.id)
        restart_bot()
    else:
        conversation_history.append({"role": "assistant", "content": chat_gpt_response})
        save_history_to_file()
        return chat_gpt_response

@client.on(events.NewMessage(pattern='.new'))
async def handle_new(event):
    if event.sender_id != allowed_user_id:
        return

    global conversation_history
    await event.edit("🫡 СЭР ДА СЭР!")
    conversation_history = []
    save_history_to_file()

@client.on(events.NewMessage)
async def handle_message(event):
    if event.message.text and event.message.text.startswith('.g'):
        user_input = event.message.text[3:].strip()
        chat_id = event.chat_id
        save_chat_id(chat_id)
        
        if event.message.sender_id != allowed_user_id:
            return
        
        await event.delete()
        msg = await event.respond("📝 Запрос: `" + user_input + "`\n\n🤖 Ожидание...")
        
        try:
            chat_gpt_response = await process_request(user_input, chat_id, msg)
            if chat_gpt_response == "...":
                await msg.edit("📝 Запрос: `" + user_input + "`\n\n😭 Ошибка")
            else:
                await msg.edit("📝 Запрос: `" + user_input + "`\n\n🤖 Ответ: " + chat_gpt_response)
        except Exception as e:
            print(f"Ошибка:", e)
            await msg.edit("😭 Ошибка")

async def handle_pending_request():
    chat_id = load_chat_id()
    if chat_id is not None and os.path.exists('time.txt'):
        with open('time.txt', 'r', encoding='utf-8') as file:
            data = json.load(file)
            user_input = data['user_input']
        os.remove('time.txt')

        message_id = load_message_id()
        if message_id:
            try:
                msg = await client.get_messages(chat_id, ids=message_id)
                await msg.delete()
            except Exception as e:
                print(f"Ошибка:", e)

        try:
            msg = await client.send_message(chat_id, "📝 Запрос: `" + user_input + "`\n\n🤖 Ожидание...")
            chat_gpt_response = await process_request(user_input, chat_id, msg)
            if chat_gpt_response == "...":
                await msg.edit("📝 Запрос: `" + user_input + "`\n\n🤖 Ошибка при обработке запроса.")
            else:
                await msg.edit("📝 Запрос: `" + user_input + "`\n\n🤖 Ответ: " + chat_gpt_response)
        except Exception as e:
            print(f"Ошибка:", e)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    load_history_from_file()
    client.start(phone)
    client.loop.run_until_complete(handle_pending_request())
    client.run_until_disconnected()
