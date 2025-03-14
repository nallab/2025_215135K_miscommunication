from flask import render_template, request, redirect, url_for
from testapp import app
from .model.openai_multi_agent import ChatFacilitator


chat_facilitator = ChatFacilitator(config_file_path="config.yaml")
agent_A_name = chat_facilitator.agent_A.name
agent_B_name = chat_facilitator.agent_B.name
agent_C_name = chat_facilitator.agent_C.name
names = {"A": agent_A_name, "B": agent_B_name, "C": agent_C_name}


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
        # 最初の3発話までは発話者が固定となっている
        if chat_facilitator.chat_counter == 1:
            return redirect(url_for("catch_talk", name=names["B"]))
        elif chat_facilitator.chat_counter == 2:
            return redirect(url_for("catch_talk", name=names["C"]))
        else:
            return redirect(url_for("check_finish_talk"))


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
            return redirect(url_for("decide_speaker"))
