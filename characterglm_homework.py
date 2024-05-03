"""
一个简单的demo，调用CharacterGLM实现角色扮演，调用CogView生成图片，调用ChatGLM生成CogView所需的prompt。

依赖：
pyjwt
requests
streamlit
zhipuai
python-dotenv

运行方式：
```bash
streamlit run characterglm_homework.py
```
"""
import os
import itertools
from typing import Iterator, Optional
import streamlit as st
from dotenv import load_dotenv
import copy
import datetime



# 通过.env文件设置环境变量
# reference: https://github.com/theskumar/python-dotenv
load_dotenv()
import api
from api import get_characterglm_response
from data_types import TextMsg, filter_text_msg

st.set_page_config(page_title="CharacterGLM API Demo", page_icon="🤖", layout="wide")
debug = os.getenv("DEBUG", "").lower() in ("1", "yes", "y", "true", "t", "on")


def update_api_key(key: Optional[str] = None):
    if debug:
        print(f'update_api_key. st.session_state["API_KEY"] = {st.session_state["API_KEY"]}, key = {key}')
    # print(f'update_api_key. st.session_state["API_KEY"] = {st.session_state["API_KEY"]}, key = {key}')
    key = key or st.session_state["API_KEY"]
    if key:
        api.API_KEY = key


# 设置API KEY
# api_key = st.sidebar.text_input("API_KEY", value=os.getenv("API_KEY", ""),
update_api_key()

# 初始化
if "history" not in st.session_state:
    st.session_state["history"] = []
if "meta" not in st.session_state:
    st.session_state["meta"] = {
        "user_info": "",
        "bot_info": "",
        "bot_name": "",
        "user_name": ""
    }


def init_session():
    st.session_state["history"] = []


# 4个输入框，设置meta的4个字段
meta_labels = {
    "bot_name": "角色名",
    "user_name": "角色名2",
    "bot_info": "角色人设",
    "user_info": "角色人设2"
}

# 2x2 layout
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        st.text_input(label="角色名", key="bot_name", on_change=lambda: st.session_state["meta"].update(
            bot_name=st.session_state["bot_name"]), help="模型所扮演的角色的名字，不可以为空")
        st.text_area(label="角色人设", key="bot_info", on_change=lambda: st.session_state["meta"].update(
            bot_info=st.session_state["bot_info"]), help="角色的详细人设信息，不可以为空")

    with col2:
        st.text_input(label="角色名2", value="", key="user_name", on_change=lambda: st.session_state["meta"].update(
            user_name=st.session_state["user_name"]), help="模型2所扮演的角色的名字，不可以为空")
        st.text_area(label="角色人设2", value="", key="user_info", on_change=lambda: st.session_state["meta"].update(
            user_info=st.session_state["user_info"]), help="角色2的详细人设信息，不可以为空")

def save_history_list_to_txt(meta, lst):
    result = ''
    for item in lst:
        role = item['role']
        content = item['content']
        character = ''
        if role == 'user':
            character = meta['user_name']
        else:
            character = meta['bot_name']
        str = f'{character}: {content}'
        print(str)
        result += f"{str}\n"
    return result



def verify_meta() -> bool:
    # 检查`角色名`和`角色人设`是否空，若为空，则弹出提醒
    if st.session_state["meta"]["bot_name"] == "" or st.session_state["meta"]["bot_info"] == "" \
            or st.session_state["meta"]["user_name"] == "" or st.session_state["meta"]["user_info"] == "":
        st.error("角色名和角色人设不能为空")
        return False
    else:
        return True


button_labels = {
    "clear_meta": "清空人设",
    "clear_history": "清空对话历史",
    "download_history": "导出对话"
}
if debug:
    button_labels.update({
        "show_api_key": "查看API_KEY",
        "show_meta": "查看meta",
        "show_history": "查看历史",
        "download_history": "导出对话"
    })
button_labels.update({
    "show_api_key": "查看API_KEY",
    "show_meta": "查看meta",
    "show_history": "查看历史"
})
# 在同一行排列按钮
with st.container():
    n_button = len(button_labels)
    cols = st.columns(n_button)
    button_key_to_col = dict(zip(button_labels.keys(), cols))

    with button_key_to_col["clear_meta"]:
        clear_meta = st.button(button_labels["clear_meta"], key="clear_meta")
        if clear_meta:
            st.session_state["meta"] = {
                "user_info": "",
                "bot_info": "",
                "bot_name": "",
                "user_name": ""
            }
            st.rerun()

    with button_key_to_col["clear_history"]:
        clear_history = st.button(button_labels["clear_history"], key="clear_history")
        if clear_history:
            init_session()
            st.rerun()

    with button_key_to_col["download_history"]:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f'history_{timestamp}.txt'
        st.download_button(
            label="下载文本文件",
            data=save_history_list_to_txt(st.session_state['meta'], st.session_state['history']),
            file_name=filename,
            mime="text/plain"
        )

    if debug:
        with button_key_to_col["show_api_key"]:
            show_api_key = st.button(button_labels["show_api_key"], key="show_api_key")
            if show_api_key:
                print(f"API_KEY = {api.API_KEY}")

        with button_key_to_col["show_meta"]:
            show_meta = st.button(button_labels["show_meta"], key="show_meta")
            if show_meta:
                print(f"meta = {st.session_state['meta']}")

        with button_key_to_col["show_history"]:
            show_history = st.button(button_labels["show_history"], key="show_history")
            if show_history:
                print(f"history = {st.session_state['history']}")
    with button_key_to_col["show_api_key"]:
        show_api_key = st.button(button_labels["show_api_key"], key="show_api_key")
        if show_api_key:
            print(f"API_KEY = {api.API_KEY}")

    with button_key_to_col["show_meta"]:
        show_meta = st.button(button_labels["show_meta"], key="show_meta")
        if show_meta:
            print(f"meta = {st.session_state['meta']}")

    with button_key_to_col["show_history"]:
        show_history = st.button(button_labels["show_history"], key="show_history")
        if show_history:
            print(f"history = {st.session_state['history']}")



# 展示对话历史
for msg in st.session_state["history"]:
    if msg["role"] == "user":
        with st.chat_message(name="user", avatar="user"):
            st.markdown(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message(name="assistant", avatar="assistant"):
            st.markdown(msg["content"])
    else:
        raise Exception("Invalid role")

with st.chat_message(name="user", avatar="user"):
    input_placeholder = st.empty()
with st.chat_message(name="assistant", avatar="assistant"):
    message_placeholder = st.empty()


def output_stream_response(response_stream: Iterator[str], placeholder):
    content = ""
    for content in itertools.accumulate(response_stream):
        # placeholder.markdown(content)
        a = 1
    return content



def start_chat():
    query = st.chat_input("开始对话吧")
    if not query:
        return
    else:
        if not verify_meta():
            return
        if not api.API_KEY:
            st.error("未设置API_KEY")
        cnt = 0
        input_placeholder.markdown(query)
        st.session_state["history"].append(TextMsg({"role": "user", "content": query}))

        while cnt < 20:
            msg_list = copy.deepcopy(filter_text_msg(st.session_state["history"]))
            who = turn_to_who_character(filter_text_msg(st.session_state["history"]))
            print(f'who:{who}')
            msg = tranform_msg_list(msg_list, who)
            meta = tranform_meta_dict(st.session_state["meta"], who)
            print(f'msg:{msg}')
            print(f'meta:{meta}')
            response_stream = get_characterglm_response(msg, meta=meta)
            bot_response = output_stream_response(response_stream, message_placeholder)
            if not bot_response:
                message_placeholder.markdown("生成出错")
                st.session_state["history"].pop()
            else:
                if who == "user_info":
                    st.session_state["history"].append(TextMsg({"role": "user", "content": bot_response}))
                    with st.chat_message(name="user", avatar="user"):
                        st.markdown(bot_response)
                else:
                    st.session_state["history"].append(TextMsg({"role": "assistant", "content": bot_response}))
                    with st.chat_message(name="assistant", avatar="assistant"):
                        st.markdown(bot_response)
            cnt += 1

def turn_to_who_character(msg_list: list) -> str:
    count_user = 0
    count_assistant = 0
    for msg in msg_list:
        if msg['role'] == 'user':
            count_user += 1
        elif msg['role'] == 'assistant':
            count_assistant += 1
    print(f'count_user:{count_user},count_assistant:{count_assistant}')
    if count_user > count_assistant:
        return 'bot_info'
    else:
        return 'user_info'

def tranform_meta_dict(meta_dict: dict, who: str) -> dict:
    meta_dict0 = {}
    if who == "user_info":
        meta_dict0 = {
            "bot_name": meta_dict['user_name'],
            "user_name": meta_dict['bot_name'],
            "bot_info": meta_dict['user_info'],
            "user_info": meta_dict['bot_info']
        }
    else:
        meta_dict0 = {
            "bot_name": meta_dict['bot_name'],
            "user_name": meta_dict['user_name'],
            "bot_info": meta_dict['bot_info'],
            "user_info": meta_dict['user_info']
        }
    return meta_dict0


# 转化对话
def tranform_msg_list(msg_list: list, who: str) -> list:
    character0 = 'assistant'
    character1 = 'user'
    # 回答者
    if who == "bot_info":
        character0 = 'user'
        character1 = 'assistant'

    # output_list = [{"role": "user", "content": item["content"]} if item['role'] == 'a' else item for item in msg_list]
    # 使用列表推导式创建新列表
    modified_list = [
        {"role": character0, "content": item["content"]} if item['role'] == "user" else
        {"role": character1, "content": item["content"]} if item['role'] == "assistant" else
        {"role": item['role'], "content": item["content"]} for item in msg_list
    ]

    return modified_list


start_chat()
# 启动方式
# streamlit run characterglm_homework.py
