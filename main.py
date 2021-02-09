import os

import enum

from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivymd.app import MDApp
from kivymd.uix.button import Button
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.list import IconRightWidget, OneLineRightIconListItem, TwoLineRightIconListItem, IRightBody
from kivymd.uix.slider import MDSlider
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


class AudioSlider(MDSlider):
    sound_loader = ObjectProperty(None)
    def on_touch_up(self, touch):
        if self.sound_loader is None:
            print('None')
            return
        if touch.grab_current == self:
            return_value = super(AudioSlider, self).on_touch_up(touch)

            self.sound_loader.seek(self.max * self.value_normalized)
            return return_value
        else:
            return super(AudioSlider, self).on_touch_up(touch)


class BL(MDBoxLayout):
    def __init__(self):
        super(BL, self).__init__()

        self.sound = SoundLoader.load('')
        self.downloading_podcast_list = []
        self.play_screen_slider_layout = self.ids.play_screen_slider_layout
        self.slider = AudioSlider(min=0, max=0, value=0, sound_loader=self.sound, pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.slider.hint = False
        self.play_screen_slider_layout.add_widget(self.slider)
        self.slider_updater = None
        self.play_screen_podcast_name_label = self.ids.play_screen_podcast_name
        self.play_screen_play_button = self.ids.play_screen_play_button
        self.STOP_ICON = 'stop-circle-outline'
        self.PLAY_ICON = 'play-circle-outline'
        self.PAUSE_ICON = 'pause-circle-outline'



    def download_btn_onclick(self):
        url = self.ids.video_url_textfield.text
        Thread(target=self.download_audio, args=(url,)).start()

    def play_btn_onclick(self):
        if self.sound is None:
            return
        if self.sound.state == 'play':
            self.play_screen_play_button.icon = self.PLAY_ICON
            self.sound.stop()
        else:
            self.play_screen_play_button.icon = self.PAUSE_ICON
            self.sound.play()
            self.sound.seek(self.slider.value)


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
        ''' Create the podcast list on Podcast Screen

        Remove the existing list, create a new list according to the current playing audio
        '''
        podcast_list = self.ids.podcast_list
        self.remove_children_from_list_widget(podcast_list)
        arr = os.listdir('download/')
        for filename in arr:
            if filename.endswith('.mp3'):
                icon = IconRightWidget(icon=self.PLAY_ICON)
                if self.sound is not None:
                    if self.sound.state == 'play':
                        current_playing_filename = self.sound.source.split('\\')[-1]
                        if current_playing_filename == filename:
                            icon = IconRightWidget(icon=self.STOP_ICON)
                list_item = OneLineRightIconListItem(text=filename, on_release=self.podcast_list_item_onclick)
                list_item.add_widget(icon)
                podcast_list.add_widget(list_item)

    def podcast_list_item_onclick(self, list_item):
        ''' OnClick function of the individual podcast list item on Podcast Screen.

        If the clicked list_item is the same as currently playing podcast, stop the playback and set self.sound to None
        Else, start the podcast from beginning.

        Args:
            list_item (OneLineRightIconListItem): The clicked podcast list item on Podcast Screen
        '''
        self.play_screen_podcast_name_label.text = list_item.text
        if self.sound is None:
            for layout in list_item.children:
                for child in layout.children:
                    if type(child) == IconRightWidget:
                        layout.remove_widget(child)
                        icon = IconRightWidget(icon=self.STOP_ICON)
                        layout.add_widget(icon)
            self.sound = SoundLoader.load(f'download/{list_item.text}')
            self.sound.play()
        else:
            current_audio = self.sound.source.split('\\')[-1]
            if self.sound.state == 'play' and list_item.text == current_audio:
                # The current playing podcast is the same as the clicked list item.
                self.sound.stop()
                self.sound.unload()
                self.sound = None
                self.play_screen_podcast_name_label.text = ''
                for layout in list_item.children:
                    for child in layout.children:
                        if type(child) == IconRightWidget:
                            layout.remove_widget(child)
                            icon = IconRightWidget(icon=self.PLAY_ICON)
                            layout.add_widget(icon)
            else:
                # The playback can either be paused or currently playing another podcast.
                # In both cases, recreate the podcast list and start the clicked podcast from beginning
                self.sound.unload()
                self.sound = SoundLoader.load(f'download/{list_item.text}')
                self.sound.play()
                self.create_podcast_list()
                for layout in list_item.children:
                    for child in layout.children:
                        if type(child) == IconRightWidget:
                            layout.remove_widget(child)
                            icon = IconRightWidget(icon=self.STOP_ICON)
                            layout.add_widget(icon)
        self.create_audio_slider()



    def create_audio_slider(self):
        ''' Create a new audio slider on Play Screen for the current playback.

        First remove the existing slider.
        If self.sound is NoneType, this means there is no audio currently playing. Create a slider that is not actionable.
        Else, create a slider which the max value matches the currently playing audio length.
        '''
        self.play_screen_slider_layout.remove_widget(self.slider)
        if self.sound is None:
            self.slider = AudioSlider(min=0, max=0, value=0, sound_loader=self.sound, pos_hint={'center_x': 0.5, 'center_y': 0.5})
        else:
            self.slider = AudioSlider(min=0, max=self.sound.length, value=0, sound_loader=self.sound, pos_hint={'center_x': 0.5, 'center_y': 0.5})
            self.slider_updater = Clock.schedule_interval(self.slider_update_func, 1)
        self.slider.hint = False
        self.play_screen_slider_layout.add_widget(self.slider)

    def slider_update_func(self, dt):
        ''' Update the position of the audio slider on Play Screen.

        There are three possible state of self.sound:
        1. self.sound is NoneType, self.slider_updater is set to None
        2. self.sound.state is 'stop', this means the audio playback has been paused. Stop the slider_updater and set
        the value to None.
        3. self.sound.state is 'play', change the position of the audio slider to match the playback position.

        '''
        if self.sound is None:
            if self.slider_updater is not None:
                self.slider_updater.cancel()
            self.slider_updater = None
            return
        if self.sound.state == 'stop':
            self.slider_updater.cancel()
            return
        self.slider.value = self.sound.get_pos()


if __name__ == "__main__":
    MyApp().run()