import os
import time
import threading
import multiprocessing

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty
from kivymd.app import MDApp
from kivymd.uix.list import MDList
from kivymd.uix.list import OneLineRightIconListItem, OneLineListItem, IconRightWidget
from kivymd.uix.button import Button
from youtube_dl import YoutubeDL
from kivy.clock import Clock
from kivymd.icon_definitions import md_icons
from kivy.core.audio import SoundLoader
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label


class Alert(Popup):
    def __init__(self, title, text):
        super(Alert, self).__init__()
        content = AnchorLayout(anchor_x='center', anchor_y='bottom')
        content.size = (Window.width / 3, Window.height / 3)
        content.add_widget(
            Label(text=text, halign='left', valign='top')
        )
        ok_button = Button(text='Ok', size_hint=(None, None), size=(Window.width / 20, Window.height / 20))
        content.add_widget(ok_button)

        popup = Popup(
            title=title,
            content=content,
            size_hint=(None, None),
            size=(Window.width / 3, Window.height / 3),
            auto_dismiss=True,
        )
        ok_button.bind(on_press=popup.dismiss)
        popup.open()

class HomeScreen(Screen):
    video_url_textfield = ObjectProperty(None)

    def test_btn_onclick(self):
        print('hello world')

    def download_btn_onclick(self):
        url = self.video_url_textfield.text
        # try:
        #     p = multiprocessing.Process(target=self.download_audio(url))
        #     p.daemon = True
        #     p.start()
        #     p.join()
        # except Exception as err:
        #     print(err)


        threading.Thread(target=self.download_audio, args=(url,)).start()



    def download_audio(self, url):
        print("in download audio")
        print(url)
        try:
            ydl_opts = {
                'format': 'best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
                'duration': 120,
                'outtmpl': 'download/%(title)s.%(ext)s',
            }
            youtube_downloader = YoutubeDL(ydl_opts)
            youtube_downloader.download([url])
            video_info = youtube_downloader.extract_info(url, download=False)
            print(video_info.get('title', None))
        except:
            Alert(title='Invalid URL', text='Failed to download the audio from the given url, please try again.')


class PodcastScreen(Screen):
    sound = SoundLoader.load('')
    current_pos = 0

    def create_list(self):
        child_list = []
        for child in self.ids.podcast_list.children:
            child_list.append(child)
        for child in child_list:
            self.ids.podcast_list.remove_widget(child)
        arr = os.listdir('download/')
        for filename in arr:
            if filename.endswith('.mp3'):
                icon = IconRightWidget(icon='play-circle-outline')
                list_item = OneLineRightIconListItem(text=filename, on_release=self.play_podcast)
                list_item.add_widget(icon)
                self.ids.podcast_list.add_widget(list_item)

    def play_podcast(self, list_item):
        if self.sound is None:
            for layout in list_item.children:
                for child in layout.children:
                    if type(child) == IconRightWidget:
                        layout.remove_widget(child)
                        icon = IconRightWidget(icon='stop-circle-outline')
                        layout.add_widget(icon)
            self.sound = SoundLoader.load(f'download/{list_item.text}')
            print(self.sound.length)
            self.sound.play()
        else:
            if self.sound.state == 'play':
                self.current_pos = self.sound.get_pos()
                self.sound.stop()
                for layout in list_item.children:
                    for child in layout.children:
                        if type(child) == IconRightWidget:
                            layout.remove_widget(child)
                            icon = IconRightWidget(icon='play-circle-outline')
                            layout.add_widget(icon)
            else:
                print(list_item.text)
                current_audio_path = self.sound.source.split('\\')
                current_audio = current_audio_path[len(current_audio_path)-1]
                if current_audio == list_item.text:
                    self.sound.play()
                    self.sound.seek(self.current_pos)
                else:
                    self.sound = SoundLoader.load(f'download/{list_item.text}')
                    self.sound.play()
                    self.current_pos = 0
                for layout in list_item.children:
                    for child in layout.children:
                        if type(child) == IconRightWidget:
                            layout.remove_widget(child)
                            icon = IconRightWidget(icon='stop-circle-outline')
                            layout.add_widget(icon)


class PlayScreen(Screen):
    pass


class MyApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Gray"
        return Builder.load_file("my.kv")


if __name__ == "__main__":
    MyApp().run()
