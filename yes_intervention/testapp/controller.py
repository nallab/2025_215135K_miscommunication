from flask import render_template, request, redirect, url_for
from testapp import app
from .model.openai_multi_agent import ChatFacilitator


chat_facilitator = ChatFacilitator(config_file_path="config.yaml")
agent_A_name = chat_facilitator.agent_A.name
agent_B_name = chat_facilitator.agent_B.name
agent_C_name = chat_facilitator.agent_C.name
agent_D_name = chat_facilitator.agent_D.name
names = {"A": agent_A_name, "B": agent_B_name, "C": agent_C_name, "D": agent_D_name}


@app.route('/')
def index():
    return redirect(url_for("catch_talk", name=names["A"]))


@app.route('/catch_talk/<string:name>', methods=['GET', 'POST'])
def catch_talk(name):
    if request.method == "GET":
        message = chat_facilitator.make_talk(name)
        return render_template("testapp/catch_talk.html", message=message, name=name, cnt=chat_facilitator.chat_counter)
    if request.method == "POST":
        remark = request.form.get('remark')
        chat_facilitator.receive_agent_output(remark, name)
        # Dが発言した場合は次にOの判定に移る
        if name == names["D"]:
            return redirect(url_for("decide_speaker"))
        # 最初の3発話までは発話者が固定となっている
        if chat_facilitator.chat_counter == 1:
            return redirect(url_for("catch_talk", name=names["B"]))
        elif chat_facilitator.chat_counter == 2:
            return redirect(url_for("catch_talk", name=names["C"]))
        else:
            return redirect(url_for("check_finish_talk"))


@app.route('/should_speak', methods=['GET', 'POST'])
def should_speak():
    if request.method == "GET":
        message = chat_facilitator.agent_D.should_speak()
        return render_template("testapp/should_speak.html", message=message)
    if request.method == "POST":
        ans_should_speak = request.form.get('should_speak')
        if ans_should_speak == "yes":
            return redirect(url_for("catch_talk", name=names["D"]))
        else:
            return redirect(url_for("decide_speaker"))


@app.route('/decide_speaker', methods=['GET', 'POST'])
def decide_speaker():
    if request.method == "GET":
        message = chat_facilitator.agent_O.decide_speaker()
        return render_template("testapp/decide_speaker.html", message=message, names=names)
    if request.method == "POST":
        next_speaker_name = request.form.get('decide_speaker')
        if next_speaker_name == names["A"]:
            return redirect(url_for("catch_talk", name=names["A"]))
        elif next_speaker_name == names["B"]:
            return redirect(url_for("catch_talk", name=names["B"]))
        else:
            return redirect(url_for("catch_talk", name=names["C"]))


@app.route('/check_end_talk', methods=['GET', 'POST'])
def check_finish_talk():
    if request.method == "GET":
        return render_template("testapp/check_finish_talk.html")
    if request.method == "POST":
        is_finish = request.form.get('is_finish')
        if is_finish == "yes":
            # 最後にログを出力
            chat_counter, memory = chat_facilitator.make_final_log()
            return render_template("testapp/result.html", chat_counter=chat_counter, memory=memory)
        else:
            return redirect(url_for("should_speak"))
