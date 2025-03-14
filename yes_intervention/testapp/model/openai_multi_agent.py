# APIを用いてマルチエージェントで会話させる
from openai import OpenAI
import yaml
import re
import logging
import datetime
import os


class OpenAiUser():
    def __init__(self, model_name: str, temperature):
        self.temperature = temperature
        self.model_name = model_name

    def use_open_ai_api(self, initial_memory: str, prompt: str):
        # openAIのAPIを使用するためのクライアント
        client = OpenAI()
        completion = client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": initial_memory},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature
        )
        initial_memory = initial_memory.replace("\n", r"\n")  # ログが見やすくなるように改行を置き換える
        prompt = prompt.replace("\n", r"\n")  # ログが見やすくなるように改行を置き換える
        api_log = {"system": initial_memory, "user": prompt}
        return completion, api_log


class MyLogger():
    def __init__(self, log_dir):
        # 実行時の日時を取得
        t_delta = datetime.timedelta(hours=9)
        JST = datetime.timezone(t_delta, 'JST')
        now = datetime.datetime.now(JST)
        # ログのパスを作成
        os.makedirs(log_dir, exist_ok=True)  # ディレクトリが存在しない場合は作成
        log_file_name = now.strftime('%Y-%m-%d-%H-%M') + ".log"
        log_path = os.path.join(log_dir, log_file_name)
        # ハンドラの作成
        fl_handler = logging.FileHandler(filename=log_path, encoding="utf-8")
        self.logger = logging.getLogger("my_logger")
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(fl_handler)

    def info(self, message):
        self.logger.info(message)


class Agent:
    def __init__(self, initial_memory: str, my_logger: MyLogger, open_ai_user: OpenAiUser):
        self.initial_memory = initial_memory
        self.memory = []
        self.open_ai_user = open_ai_user
        self.my_logger = my_logger

    def add_memory(self, add_chat):
        self.memory.append(add_chat)

    def get_memory(self):
        memory_text = "\n".join(self.memory)
        return memory_text

    def get_initial_memory(self):
        return self.initial_memory


class Speaker(Agent):
    def __init__(self, name, initial_memory, my_logger, open_ai_user):
        super().__init__(initial_memory, my_logger, open_ai_user)
        self.name = name

    def speak(self, cnt):
        prompt = " What would you say ? You would say : "
        if cnt != 1:  # 最初(cnt==1)のときはget_memory()しても空の文字列が返ってくるので、改行を含まないようにする
            prompt = self.get_memory() + "\n" + prompt
        completion, api_log = self.open_ai_user.use_open_ai_api(self.get_initial_memory(), prompt)
        self.my_logger.info(f"{self.name}の返信: {completion.choices[0].message.content}")
        self.my_logger.info(f"system: {api_log['system']}")
        self.my_logger.info(f"user: {api_log['user']}")
        return completion.choices[0].message.content


class Intervenor(Speaker):
    def __init__(self, name, initial_memory, my_logger, open_ai_user):
        super().__init__(name, initial_memory, my_logger, open_ai_user)

    def should_speak(self):
        prompt = self.get_memory() + "\n" + " Should you speak now ? Yes / No : "
        completion, api_log = self.open_ai_user.use_open_ai_api(self.get_initial_memory(), prompt)
        self.my_logger.info(f"{self.name}の返信: {completion.choices[0].message.content}")
        self.my_logger.info(f"system: {api_log['system']}")
        self.my_logger.info(f"user: {api_log['user']}")
        return completion.choices[0].message.content


class Oracle(Agent):
    def __init__(self, initial_memory, my_logger, open_ai_user, agent_A, agent_B, agent_C):
        super().__init__(initial_memory, my_logger, open_ai_user)
        self.agent_A = agent_A
        self.agent_B = agent_B
        self.agent_C = agent_C

    def decide_speaker(self):
        prompt = self.get_memory() + "\n" + " Who is most likely to speak now ? Answer in one word from Alice , Bob , and Claire : "
        completion, api_log = self.open_ai_user.use_open_ai_api(self.get_initial_memory(), prompt)
        self.my_logger.info(f"Oの返信: {completion.choices[0].message.content}")
        self.my_logger.info(f"system: {api_log['system']}")
        self.my_logger.info(f"user: {api_log['user']}")
        return completion.choices[0].message.content


# 会話の進行を担当するクラス
class ChatFacilitator:
    def __init__(self, config_file_path) -> None:
        self.chat_counter = 0
        self.all_chats = []
        # yamlの読み込み
        with open(config_file_path, 'r') as file:
            self.config = yaml.safe_load(file)

        self.my_logger = MyLogger(log_dir=self.config["log_dir_name"])
        self.open_ai_user = OpenAiUser(self.config["open_ai_model"], self.config["temperature"])

        # 各agentの作成
        A_initial_memory = self.make_initial_memory_of_A_and_B(self.config["word1"], self.config["word2"], self.config["agent1"]["initial_memory"])
        B_initial_memory = self.make_initial_memory_of_A_and_B(self.config["word1"], self.config["word2"], self.config["agent2"]["initial_memory"])

        self.agent_A = Speaker(self.config["agent1"]["name"], A_initial_memory, self.my_logger, self.open_ai_user)
        self.agent_B = Speaker(self.config["agent2"]["name"], B_initial_memory, self.my_logger, self.open_ai_user)
        self.agent_C = Speaker(self.config["agent3"]["name"], self.config["agent3"]["initial_memory"], self.my_logger, self.open_ai_user)
        self.agent_D = Intervenor(self.config["meta_agent"]["name"], self.config["meta_agent"]["initial_memory"], self.my_logger, self.open_ai_user)
        self.agent_O = Oracle(self.config["oracle"]["initial_memory"], self.my_logger, self.open_ai_user, self.agent_A, self.agent_B, self.agent_C)

    def make_initial_memory_of_A_and_B(self, word1: str, word2: str, initial_memory: str) -> str:
        new_initial_memory = re.sub(r'\$\{word1\}', word1, initial_memory)
        new_initial_memory = re.sub(r'\$\{word2\}', word2, new_initial_memory)
        return new_initial_memory

    def add_memories(self, add_chat: str) -> None:
        agents = [self.agent_A, self.agent_B, self.agent_C, self.agent_D, self.agent_O]
        for agent in agents:
            agent.add_memory(add_chat)

    def receive_agent_output(self, output_text: str, return_agent_name: str) -> None:
        output_text = " " + return_agent_name + ": " + output_text
        self.add_memories(output_text)
        self.all_chats.append(output_text)

    def make_talk(self, speaker_name: str):
        self.chat_counter += 1
        speaker = self.change_name_to_speaker(speaker_name)
        message = speaker.speak(self.chat_counter)
        return message

    def change_name_to_speaker(self, speaker_name: str) -> Speaker:
        speakers = [self.agent_A, self.agent_B, self.agent_C, self.agent_D]
        for speaker in speakers:
            if speaker_name == speaker.name:
                return speaker

    def make_final_log(self):
        chat_counter = self.chat_counter
        memory = ""
        for i, chat in enumerate(self.all_chats):
            memory += f"{i+1}. {chat} \n"
        self.my_logger.info(f"発話回数: {chat_counter}")
        self.my_logger.info(memory)
        # 再実行用のログを出力(後日実装予定)
        output_dict = {}
        output_dict["speak_num"] = chat_counter
        output_dict["all_chats"] = "\n".join(self.all_chats)
        self.my_logger.info(output_dict)

        return chat_counter, memory
