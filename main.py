import os

import enum

from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.popup import Popup
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.list import IconRightWidget, OneLineRightIconListItem, TwoLineRightIconListItem, IRightBody
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.uix.label import Label
from kivymd.uix.button import Button
from threading import Thread
from youtube_dl import YoutubeDL


class MyApp(MDApp):
    def __init__(self, **kwargs):
        self.title = "Youtube 2 Podcast"
        super().__init__(**kwargs)

    def build(self):
        return BL()


class DownloadAlert(Popup):
    def __init__(self, title, text):
        super(DownloadAlert, self).__init__()
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

class ListItemWithPercentage(TwoLineRightIconListItem):
    '''Custom list item.'''


class RightLabel(IRightBody, MDLabel):
    '''Custom right container.'''


class DownloadStatus(enum.Enum):
    Downloading = 1
    Processing = 2
    Finish = 3
    Error = 4


class DownloadingPodcast:
    def __init__(self, title, download_status):
        self.title = title
        self.download_status = download_status
        self.download_percentage = '0%'


class BL(MDBoxLayout):
    sound = SoundLoader.load('')
    current_sound_pos = 0
    downloading_podcast_list = []


    def download_btn_onclick(self):
        url = self.ids.video_url_textfield.text
        Thread(target=self.download_audio, args=(url,)).start()

    def callable_hook(self, response):
        filename = response['filename'].split('\\')
        title = filename[len(filename) - 1]
        title = title[:-4]  # remove .mp4
        for downloading_podcast in self.downloading_podcast_list:
            if downloading_podcast.title == title:
                current_downloading_podcast = downloading_podcast
            break
        if response['status'] == 'downloading':
            current_downloading_podcast.download_percentage = response['_percent_str']
            self.create_download_list()
        if response['status'] == 'finished':
            current_downloading_podcast.download_status = DownloadStatus.Finish
            current_downloading_podcast.download_percentage = ''
            self.create_download_list()
            print('end of download')
        if response['status'] == 'error':
            pass

    def download_audio(self, url):
        try:
            ydl_opts = {
                'format': 'best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
                'duration': 120,
                'outtmpl': 'download/%(title)s.%(ext)s',
                'progress_hooks': [self.callable_hook],
            }
            youtube_downloader = YoutubeDL(ydl_opts)
            video_info = youtube_downloader.extract_info(url, download=False)
            current_downloading_podcast = DownloadingPodcast(video_info.get('title', None), DownloadStatus.Downloading)
            self.downloading_podcast_list.append(current_downloading_podcast)
            self.create_download_list()
            youtube_downloader.download([url])
        except:
            DownloadAlert(title='Invalid URL', text='Failed to download the audio from the given url, please try again.')

    def create_download_list(self):
        download_list = self.ids.download_list
        self.remove_children_from_list_widget(download_list)
        for downloading_podcast in self.downloading_podcast_list:
            title = downloading_podcast.title
            status = downloading_podcast.download_status.name
            list_item = ListItemWithPercentage(text=title, secondary_text=status)
            if downloading_podcast.download_status == DownloadStatus.Downloading:
                list_item.ids.download_status_progress.text = downloading_podcast.download_percentage
            download_list.add_widget(list_item)

    def remove_children_from_list_widget(self, mdList):
        child_list = []
        for child in mdList.children:
            child_list.append(child)
        for child in child_list:
            mdList.remove_widget(child)


    def create_podcast_list(self):
        podcast_list = self.ids.podcast_list
        self.remove_children_from_list_widget(podcast_list)
        arr = os.listdir('download/')
        for filename in arr:
            if filename.endswith('.mp3'):
                icon = IconRightWidget(icon='play-circle-outline')
                list_item = OneLineRightIconListItem(text=filename, on_release=self.play_podcast)
                list_item.add_widget(icon)
                podcast_list.add_widget(list_item)

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
                self.current_sound_pos = self.sound.get_pos()
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
                    self.sound.seek(self.current_sound_pos)
                else:
                    self.sound = SoundLoader.load(f'download/{list_item.text}')
                    self.sound.play()
                    self.current_sound_pos = 0
                for layout in list_item.children:
                    for child in layout.children:
                        if type(child) == IconRightWidget:
                            layout.remove_widget(child)
                            icon = IconRightWidget(icon='stop-circle-outline')
                            layout.add_widget(icon)

if __name__ == "__main__":
    MyApp().run()