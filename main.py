import random
import logging
from pathlib import Path

import csv
import yaml
import requests
import vk_api
from vk_api import VkUpload
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from gtts import gTTS
from datetime import datetime
from csv import reader

from functions import get_random_file, request_current_weather


BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR.joinpath("config.yaml")
IMG_DIR = BASE_DIR.joinpath("img")
VIDEO_DIR = BASE_DIR.joinpath("video")
MUSIC_DIR = BASE_DIR.joinpath("music")
DOC_DIR = BASE_DIR.joinpath("documents")


with open(CONFIG_PATH, encoding="utf-8") as ymlFile:
    config = yaml.load(ymlFile.read(), Loader=yaml.Loader)

logging.basicConfig(
    format='%(asctime)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S',
    level=logging.INFO
)

logger = logging.getLogger('vk_api')
logger.disabled = True


authorize = vk_api.VkApi(token=config["group"]["group_token"])

longpoll = VkBotLongPoll(authorize, group_id=config["group"]["group_id"])
bot_upload = VkUpload(authorize)
bot = authorize.get_api()


vk_session = vk_api.VkApi(token=config["user"]["user_token"])

vk = vk_session.get_api()
vk_upload = VkUpload(vk_session)

logging.info("Авторизация прошла успешно")


class Utils:
    def get_random_member(self, chat_id):
        members = bot.messages.getConversationMembers(
            peer_id=2000000000 + chat_id,
            group_id=config["group"]["group_id"]
        )["items"]
        member_id = random.choice(members)["member_id"]
        return member_id

    def get_username(self, user_id):
        user_info = vk.users.get(user_ids=user_id)[0]
        username = "{} {}".format(
            user_info["first_name"],
            user_info["last_name"]
        )
        return f"[id{user_id}|{username}]"

    def get_group_name(self, group_id):
        group_info = vk.groups.getById(group_id=-group_id)[0]
        return f"[club{group_info['id']}|{group_info['name']}]"


class VkBot:
    def write_message(self, message="", attachment=""):
        bot.messages.send(
            chat_id=self.chat_id,
            message=message,
            attachment=attachment,
            random_id=get_random_id()
        )

    def say_hello(self):
        user_info = vk.users.get(user_id=self.sender_id)[0]
        username = user_info["first_name"]
        message = f"Привет, {username}!"
        x = random.randint(1, 2)
        if x == 1:
            self.write_message(message=message)

        else:

            tts = gTTS(text=message, lang="ru", lang_check=True)
            file_path = BASE_DIR.joinpath("audio.mp3")
            tts.save(file_path)

            self.send_file("audio.mp3", file_type="audio_message")

            file_path.unlink()

    def send_file(self, file, file_type):
        attachment = ""
        if file_type == "photo":
            response = bot_upload.photo_messages(
                photos=file,
                peer_id=2000000000 + self.chat_id
            )[0]
            attachment = "photo{}_{}".format(response["owner_id"], response["photos_id"])

        elif file_type == "video":
            response = vk_upload.video(video_file=file, name="Видео")
            attachment = "video{}_{}".format(response["owner_id"], response["video_id"])

        elif file_type == "audio":
            song_data = str(file.name)[:-3].split(" - ")
            response = vk_upload.audio(
                audio=str(file),
                artist=song_data[0],
                title=song_data[1]
            )
            attachment = "audio{}_{}".format(response["owner_id"], response["id"])

        elif file_type == "audio_message":
            response = bot_upload.audio_message(
                audio="audio.mp3",
                peer_id=2000000000 + self.chat_id
            )["audio_message"]
            attachment = "doc{}_{}".format(response["owner_id"], response["audio_id"])

        elif file_type == "doc":
            response = bot_upload.document_message(
                doc=file,
                title="doc",
                peer_id=2000000000 + self.chat_id
            )["doc"]
            attachment = "doc{}_{}".format(response["owner_id"], response["id"])
        self.write_message(attachment=attachment)

    def add_to_db(self):
        with open("db.csv", 'w', newline='') as f:
            cursor = csv.writer(f)
            cursor.writerow([f'{datetime.today():%d-%B-%Y}'])
            f.close()

    def from_db(self):
        with open("db.csv", 'r', newline='') as f:
            writer_object = reader(f)
            return list(writer_object)[-1]

    def check_message(self, received_message):
        if received_message.lower() == "привет":
            self.say_hello()

        elif received_message.lower() == "видео":
            video = get_random_file(VIDEO_DIR)
            self.send_file(
                file=str(video),
                file_type="video"
            )

        elif received_message.lower() == "документ":
            document = get_random_file(DOC_DIR)
            self.send_file(
                file=str(document),
                file_type="doc"
            )

        elif received_message[:3].lower() == "кто":
            member_id = utils.get_random_member(chat_id=self.chat_id)
            phrases = ["Я думаю, это ", "Однозначно это ", "Скорее всего, это ", "Это ты"]
            message = random.choice(phrases)
            if message != "Это ты":
                if member_id > 0:
                    message += utils.get_username(member_id)
                else:
                    message += utils.get_group_name(member_id)
            self.write_message(message)

        elif received_message[:6].lower() == "погода":
            pg, tp, sp = request_current_weather(6696767)
            self.write_message(pg)
            self.write_message(tp)
            self.write_message(sp)

        elif received_message.lower() == "запомни время":
            self.add_to_db()

        elif received_message.lower() == "вспомни время" or received_message.lower() == "время":
            mes = self.from_db()
            self.write_message(mes)

    def listen(self):
        while True:
            try:
                for event in longpoll.listen():
                    if event.type == VkBotEventType.MESSAGE_NEW and event.from_chat and event.message.get("text") != "":
                        received_message = event.message.get("text").lower()
                        self.chat_id = event.chat_id
                        self.sender_id = event.message.get("from_id")
                        self.check_message(received_message)
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
                print(e)
                logging.info("Перезапуск бота")

    def run(self):
        logging.info("Бот запущен")
        self.listen()


if __name__ == "__main__":
    vkbot = VkBot()
    utils = Utils()
    vkbot.run()
