from tkinter import (
    Tk,
    Frame,
    Label,
    BOTH,
    PhotoImage,
    Button,
    Toplevel,
    Text,
    END,
    Checkbutton,
    BooleanVar,
    filedialog
)
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime
import re
import aiohttp
# import hashlib
from PIL import Image, ImageTk
from threading import Thread    
from os.path import join as pathjoin, dirname, basename, exists
from os import getenv, mkdir
from requests import get
import tempfile
from base64 import b64decode
import pygame
# import sys
from io import StringIO, BytesIO
from json import load, dump
from webbrowser import open as open_url
from time import sleep as slp

#color
G = "\033[30m"
r = "\033[31m"
g = "\033[32m"
y = "\033[33m"
b = "\033[34m"
p = "\033[35m"
c = "\033[36m"
w = "\033[37m"

# config
output: bool = True
single_refreshms: int = 2
PADDING: int = 5
refreshms: int = 500
all_refreshms: int = 2
dev_update: int = 100
image_base64_link: str = "https://pastebin.com/raw/KHfksC8W"
is_first_run = True

# Advanced Config
localappdata = getenv("LOCALAPPDATA")
config_saving_path = localappdata + "\\ExpTech_Image\\config.json"
default_config = {
    "sound": {
        "intensity": False,
        "eew": False,
        "report": False,
        "lpgm": False,
    },
    "window": {
        "intensity": False,
        "eew": False,
        "report": False,
        "lpgm": False,
    },
    "save": {
        "intensity": False,
        "eew": False,
        "report": False,
        "lpgm": False,
    },
    "image_saving_path": {
        "intensity": localappdata + "\\ExpTech_Image\\intensity", 
        "eew": localappdata + "\\ExpTech_Image\\eew",
        "report": localappdata + "\\ExpTech_Image\\report",
        "lpgm": localappdata + "\\ExpTech_Image\\lpgm",
    }
}


if not exists(localappdata + "\\ExpTech_Image"):
    mkdir(localappdata + "\\ExpTech_Image")
if not exists(config_saving_path):
    with open(config_saving_path, "w", encoding="utf-8") as file:
        dump(default_config, file, ensure_ascii=False, indent=4)


base_urls = [
    "https://api-1.exptech.dev/file/images/intensity",
    "https://api-1.exptech.dev/file/images/eew",
    "https://api-1.exptech.dev/file/images/report",
    "https://api-1.exptech.dev/file/images/lpgm",
]

sounds = {
    "eew": pathjoin(dirname(__file__), "eew.wav"),
    "intensity": pathjoin(dirname(__file__), "intensity.wav"),
    "report": pathjoin(dirname(__file__), "report.wav"),
    "lpgm": pathjoin(dirname(__file__), "lpgm.wav"),
}

image_path = None

def download_and_save_image():
    global image_path
    try:
        response = get(image_base64_link)
        if response.status_code == 200:
            temp_dir = tempfile.gettempdir()
            image_path = pathjoin(temp_dir, "ExpTech.png")
            with open(image_path, "wb") as file:
                file.write(b64decode(response.text))
        else:
            print(f"{r}下載圖片時發生錯誤：{response.status_code}{w}")
            image_path = None
    except Exception as e:
        print(f"{r}下載圖片時發生錯誤：{e}{w}")
        image_path = None

download_and_save_image()

def update_image(type=None, url=None):
    async def update_image_async(type=None, url=None, sound=False):
        async with aiohttp.ClientSession() as session:
            if url is None and type is not None:
                if type == "all":
                    # 更新所有四張圖片
                    tasks = [process_base_url(session, base_url, sound=False) for base_url in base_urls]
                    await asyncio.gather(*tasks)
                elif type in sounds:
                    # 更新單張對應的圖片
                    url = next(u for u in base_urls if type in u)
                    await process_base_url(session, url, sound=False)
            elif url is not None:
                await process_base_url(session, url, sound)

    Thread(target=asyncio.run, args=(update_image_async(type, url),)).start()

def show_single_image(url):
    for base_url in base_urls:
        frame = image_frames[base_url]
        if base_url == url:
            frame.grid(row=0, column=0, sticky="nsew")
            frame.grid_configure(padx=0, pady=0)
        else:
            frame.grid_forget()

    main_frame.grid_rowconfigure(0, weight=1)
    main_frame.grid_columnconfigure(0, weight=1)

    window.after(single_refreshms, lambda: update_image_size(single=True))

def show_all_images():
    for i, base_url in enumerate(base_urls):
        frame = image_frames[base_url]
        frame.grid(row=i // 2, column=i % 2, sticky="nsew")
        frame.grid_configure(padx=PADDING, pady=PADDING)
    window.after(all_refreshms, update_image_size)

window = Tk()

last_get_pictures = {key: [] for key in [url.split("/")[-1] for url in base_urls]}


def set_window():
    global image_path
    pygame.mixer.init()
    window.title("ExpTech Image v2.1-pre.8")
    window.geometry("888x650")
    window.resizable(False, False)
    window.config(bg="#1f1f1f")
    if image_path:
        window.iconphoto(False, PhotoImage(file=image_path))


def set_button():
    button_frame = Frame(window, bg="#1f1f1f")
    button_frame.pack(side="top", fill="x", padx=PADDING, pady=PADDING)

    buttons = [
        ("總覽", lambda: (show_all_images(), update_image("all"))),
        ("震度速報", lambda: (show_single_image(next(u for u in base_urls if "intensity" in u)), update_image("intensity"))),
        ("地震速報", lambda: (show_single_image(next(u for u in base_urls if "eew" in u)), update_image("eew"))),
        ("地震報告", lambda: (show_single_image(next(u for u in base_urls if "report" in u)), update_image("report"))),
        ("長週期的震動", lambda: (show_single_image(next(u for u in base_urls if "lpgm" in u)), update_image("lpgm"))),
        # ("開啟音效", lambda: (switch_sound())),
        ("設定", lambda: (setting())),
        ("Github", lambda: (open_url("https://github.com/2008-04-03/ExpTech_Image"))),
    ]

    for text, command in buttons:
        btn = Button(
            button_frame,
            text=text,
            command=command,
            bg="#1f1f1f",
            fg="#ffffff",
            activebackground="#1f1f1f",
            activeforeground="#ffffff",
        )
        btn.pack(side="left", expand=True, fill="both", padx=5)

    global sound_btn
    sound_btn = button_frame.winfo_children()[-2]

def load_config() -> dict:
    with open(config_saving_path, "r", encoding="utf-8") as file:
        return load(file)

def save_config(data: dict):
    with open(config_saving_path, "w", encoding="utf-8") as file:
        dump(data, file, ensure_ascii=False, indent=4)

def save_sound_data():
    config = load_config()
    config["sound"]["intensity"] = intensity_vars[0].get()
    config["sound"]["eew"] = eew_vars[0].get()
    config["sound"]["report"] = report_vars[0].get()
    config["sound"]["lpgm"] = lpgm_vars[0].get()
    save_config(config)

def save_window_data():
    config = load_config()
    config["window"]["intensity"] = intensity_vars[1].get()
    config["window"]["eew"] = eew_vars[1].get()
    config["window"]["report"] = report_vars[1].get()
    config["window"]["lpgm"] = lpgm_vars[1].get()
    save_config(config)

def save_save_data():
    config = load_config()
    config["save"]["intensity"] = intensity_vars[2].get()
    config["save"]["eew"] = eew_vars[2].get()
    config["save"]["report"] = report_vars[2].get()
    config["save"]["lpgm"] = lpgm_vars[2].get()
    save_config(config)

def save_all_data():
    save_sound_data()
    save_window_data()
    save_save_data()

setting_window = None

def setting() -> None:
    global setting_window, intensity_vars, eew_vars, report_vars, lpgm_vars
    global image_path
    if setting_window is not None and setting_window.winfo_exists():
        setting_window.lift()
        setting_window.focus_force()
        if setting_window.state() == 'iconic':
            setting_window.deiconify()
            setting_window.attributes('-topmost', True)
            setting_window.attributes('-topmost', False)
    else:
        setting_window = Toplevel(window)
        setting_window.title("設定")
        setting_window.geometry("400x300")
        setting_window.resizable(False, False)
        setting_window.config(bg="#1f1f1f")
        if image_path:
            setting_window.iconphoto(False, PhotoImage(file=image_path))
        
        # 創建主框架
        main_frame = Frame(setting_window, bg="#1f1f1f")
        main_frame.pack(expand=True, fill=BOTH, padx=10, pady=10)

        # 創建標題行
        title_frame = Frame(main_frame, bg="#1f1f1f")
        title_frame.grid(row=0, column=1, columnspan=3, sticky="ew")
        
        titles = ["音效", "彈跳視窗", "儲存圖片"]
        for i, title in enumerate(titles):
            Label(title_frame, text=title, bg="#1f1f1f", fg="#ffffff").grid(row=0, column=i, padx=5, pady=5)
        
        # check_button_options = ["sound", "window", "save"]
        check_button_options: list[str] = [key for key in default_config.keys() if key != "image_saving_path"]
        
        def switch_all(option):
            if option not in check_button_options:
                return
            if option == "sound":
                intensity_checkbuttons[0].invoke()
                eew_checkbuttons[0].invoke()
                report_checkbuttons[0].invoke()
                lpgm_checkbuttons[0].invoke()
            elif option == "window":
                intensity_checkbuttons[1].invoke()
                eew_checkbuttons[1].invoke()
                report_checkbuttons[1].invoke()
                lpgm_checkbuttons[1].invoke()
            else:
                intensity_checkbuttons[2].invoke()
                eew_checkbuttons[2].invoke()
                report_checkbuttons[2].invoke()
                lpgm_checkbuttons[2].invoke()

        # 創建全部開啟按鈕
        Button(title_frame, text="反向選擇", bg="#2f2f2f", fg="#ffffff", command=lambda: switch_all("sound"), activebackground="#2f2f2f", activeforeground="#ffffff").grid(row=1, column=0, padx=5, pady=5)
        Button(title_frame, text="反向選擇", bg="#2f2f2f", fg="#ffffff", command=lambda: switch_all("window"), activebackground="#2f2f2f", activeforeground="#ffffff").grid(row=1, column=1, padx=5, pady=5)
        Button(title_frame, text="反向選擇", bg="#2f2f2f", fg="#ffffff", command=lambda: switch_all("save"), activebackground="#2f2f2f", activeforeground="#ffffff").grid(row=1, column=2, padx=5, pady=5)

        # 創建選項行
        intensity_vars = [BooleanVar() for _ in range(3)]
        eew_vars = [BooleanVar() for _ in range(3)]
        report_vars = [BooleanVar() for _ in range(3)]
        lpgm_vars = [BooleanVar() for _ in range(3)]
        
        intensity_checkbuttons = []
        eew_checkbuttons = []
        report_checkbuttons = []
        lpgm_checkbuttons = []
        options = ["震度速報", "地震速報", "地震報告", "長週期的震動"]
        conf_options = ["intensity", "eew", "report", "lpgm"]

        # 讀取config.json並設置對應的BooleanVar
        configdata = load_config()
        for i, option in enumerate(options):
            for j, setting_type in enumerate(check_button_options):
                checkbutton_status = configdata.get(setting_type, {}).get(conf_options[i], False)
                if option == "震度速報":
                    intensity_vars[j].set(checkbutton_status)
                elif option == "地震速報":
                    eew_vars[j].set(checkbutton_status)
                elif option == "地震報告":
                    report_vars[j].set(checkbutton_status)
                elif option == "長週期的震動":
                    lpgm_vars[j].set(checkbutton_status)

        for i, option in enumerate(options):
            Label(main_frame, text=option, bg="#1f1f1f", fg="#ffffff").grid(row=i+1, column=0, sticky="w", padx=5, pady=5)
            for j in range(3):
                if option == "震度速報":
                    cb = Checkbutton(main_frame, bg="#1f1f1f", fg="#ffffff", selectcolor="#1f1f1f", command=save_all_data, activebackground="#1f1f1f", variable=intensity_vars[j])
                    cb.grid(row=i+1, column=j+1, padx=5, pady=5)
                    intensity_checkbuttons.append(cb)
                elif option == "地震速報":
                    cb = Checkbutton(main_frame, bg="#1f1f1f", fg="#ffffff", selectcolor="#1f1f1f", command=save_all_data, activebackground="#1f1f1f", variable=eew_vars[j])
                    cb.grid(row=i+1, column=j+1, padx=5, pady=5)
                    eew_checkbuttons.append(cb)
                elif option == "地震報告":
                    cb = Checkbutton(main_frame, bg="#1f1f1f", fg="#ffffff", selectcolor="#1f1f1f", command=save_all_data, activebackground="#1f1f1f", variable=report_vars[j])
                    cb.grid(row=i+1, column=j+1, padx=5, pady=5)
                    report_checkbuttons.append(cb)
                elif option == "長週期的震動":
                    cb = Checkbutton(main_frame, bg="#1f1f1f", fg="#ffffff", selectcolor="#1f1f1f", command=save_all_data, activebackground="#1f1f1f", variable=lpgm_vars[j])
                    cb.grid(row=i+1, column=j+1, padx=5, pady=5)
                    lpgm_checkbuttons.append(cb)

        # Button(main_frame, text="Save", bg="#2f2f2f", fg="#ffffff", command=save_sound_data, activebackground="#2f2f2f", activeforeground="#ffffff").grid(row=4, column=0, padx=5, pady=5)

        # 設置列和行的權重
        for i in range(5):
            main_frame.grid_rowconfigure(i, weight=1)
        for i in range(4):
            main_frame.grid_columnconfigure(i, weight=1)

thread = False
# last_hashes = {url: None for url in base_urls}
image_labels = {}
current_images = {}

def create_image_labels():
    global main_frame, image_frames
    main_frame = Frame(window, bg="#1f1f1f")
    main_frame.pack(expand=True, fill=BOTH, padx=PADDING, pady=PADDING)

    image_frames = {}
    for i, base_url in enumerate(base_urls):
        frame = Frame(main_frame, bg="#1f1f1f")
        frame.grid(row=i // 2, column=i % 2, sticky="nsew", padx=PADDING, pady=PADDING)
        image_frames[base_url] = frame

        label = Label(frame, bg="#1f1f1f")
        label.pack(expand=True, fill=BOTH)
        image_labels[base_url] = label

    for i in range(2):
        main_frame.grid_rowconfigure(i, weight=1)
        main_frame.grid_columnconfigure(i, weight=1)

set_window()
set_button()
create_image_labels()

async def get_latest_image_url(session, base_url):
    try:
        async with session.get(base_url) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                links = [
                    a["href"]
                    for a in soup.find_all("a")
                    if a["href"].endswith(".jpg") and a["href"] != "CWAEEW1-1.jpg"
                ]

                if "report" in base_url:
                    latest_image = get_latest_report_image(links)
                else:
                    latest_image = max(links) if links else None

                if latest_image:
                    return f"{base_url}/{latest_image}"
                else:
                    print(f"{r}No .jpg links found at {base_url}{w}")
            else:
                print(f"{r}Received status code {response.status} from {base_url}{w}")
    except Exception as e:
        print(f"{r}Error while fetching {base_url}: {str(e)}{w}")
    return None

def get_latest_report_image(links):
    pattern = r"(\d{4}-\d{4}-\d{6})\.jpg"
    valid_images = []
    for link in links:
        match = re.search(pattern, link)
        if match:
            date_str = match.group(1)
            try:
                date = datetime.strptime(date_str, "%Y-%m%d-%H%M%S")
                valid_images.append((date, link))
            except ValueError:
                continue

    if valid_images:
        return max(valid_images, key=lambda x: x[0])[1]
    return None

async def fetch_image(session, url):
    async with session.get(url) as response:
        if response.status == 200:
            return await response.read()
    return None

def resize_image(image, width, height):
    aspect_ratio = image.width / image.height
    new_width = width
    new_height = int(new_width / aspect_ratio)

    if new_height > height:
        new_height = height
        new_width = int(new_height * aspect_ratio)

    return image.resize((new_width, new_height), Image.LANCZOS)

def update_image_size(single=False):
    button_height = 50
    if single:
        width = window.winfo_width() - PADDING * 2
        height = window.winfo_height() - button_height - PADDING * 3
    else:
        width = (window.winfo_width() - PADDING * 3) // 2
        height = (window.winfo_height() - button_height - PADDING * 4) // 2

    for url in base_urls:
        if url in current_images:
            image = current_images[url]
            resized_image = resize_image(image, width, height)
            photo = ImageTk.PhotoImage(resized_image)

            label = image_labels[url]
            label.config(image=photo)
            label.image = photo

    main_frame.config(
        width=window.winfo_width() - PADDING * 2,
        height=window.winfo_height() - button_height - PADDING * 3,
    )

    for frame in image_frames.values():
        if frame.winfo_viewable():
            frame.config(width=width, height=height)
            frame.pack_propagate(False)

            label = frame.winfo_children()[0]
            label.place(relx=0.5, rely=0.5, anchor="center")

def show_image(base_url, image_data):
    image = Image.open(BytesIO(image_data))
    current_images[base_url] = image

    single = len([f for f in image_frames.values() if f.winfo_viewable()]) == 1

    button_height = 50
    if single:
        width = window.winfo_width() - PADDING * 2
        height = window.winfo_height() - button_height - PADDING * 2
    else:
        width = (window.winfo_width() - PADDING * 3) // 2
        height = (window.winfo_height() - button_height - PADDING * 3) // 2

    resized_image = resize_image(image, width, height)
    photo = ImageTk.PhotoImage(resized_image)

    label = image_labels[base_url]
    label.config(image=photo)
    label.image = photo

    frame = image_frames[base_url]
    frame.pack_propagate(False)
    frame.config(width=width, height=height)
    label.place(relx=0.5, rely=0.5, anchor="center")

# last_sent_urls = {url: None for url in base_urls}

async def process_base_url(session, base_url, sound=True):
    global thread
    global is_first_run
    try:
        latest_image_url = await get_latest_image_url(session, base_url)
        # if latest_image_url and latest_image_url != last_sent_urls[base_url]:
        if latest_image_url:
            image_data = await fetch_image(session, latest_image_url)       
            if latest_image_url:
                image_data = await fetch_image(session, latest_image_url)
                if image_data:
                    # current_hash = hashlib.md5(image_data).hexdigest()
                    typeofimage = base_url.split("/")[-1]
                    filename = latest_image_url.split("/")[-1]
                    try:
                        storedfilenames = last_get_pictures[typeofimage]
                    except IndexError:
                        storedfilenames = None
                    # if (current_hash != last_hashes[base_url]) and storedfilename != filename:
                    if storedfilenames is None or filename not in storedfilenames:
                        # last_hashes[base_url] = current_hash
                        last_get_pictures[typeofimage].append(filename)
                        if len(last_get_pictures[typeofimage]) > 5:
                            last_get_pictures[typeofimage].pop(0)
                        show_image(base_url, image_data)
                        # if is_sound and sound:
                        configdata = load_config()
                        if is_first_run:
                            return
                        else:
                            if configdata["sound"][typeofimage] and sound:
                                sound_file = sounds[typeofimage]
                                pygame.mixer.Sound(sound_file).play()
                            if configdata["window"][typeofimage]:
                                window.lift()
                                window.focus_force()
                                window.deiconify()
                                window.attributes('-topmost', True)
                                window.attributes('-topmost', False)
    except Exception as e:
        print(f"{r}處理 {base_url} 時出錯: {e}{w}")

async def check_updates():
    global thread
    async with aiohttp.ClientSession() as session:
        tasks = [process_base_url(session, base_url) for base_url in base_urls]
        await asyncio.gather(*tasks)
        thread = False

def schedule_check():
    global thread
    if not thread:
        run_thread = Thread(target=asyncio.run, args=(check_updates(),))
        run_thread.start()
        thread = True
    window.after(refreshms, schedule_check)

schedule_check()

def on_closing():
    pygame.mixer.music.unload()
    window.destroy()

window.protocol("WM_DELETE_WINDOW", on_closing)

try:
    def set_is_first_run_false():
        global is_first_run
        is_first_run = False
    window.after(5000, set_is_first_run_false)
    window.mainloop()
except KeyboardInterrupt:
    pass