from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.utils import platform
from kivy.uix.image import Image
from kivy.uix.label import Label

if platform == "android":
    from jnius import autoclass, cast
    from android.runnable import run_on_ui_thread
    from android import activity

class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.webview_loaded = False
        self.url = "https://codev-ui.vercel.app"
        self.start_x = 0

        # Splash screen
        self.splash = Image(source='splash.png')
        self.add_widget(self.splash)

        # Navigation buttons
        self.nav_bar = BoxLayout(size_hint_y=0.1)
        self.nav_bar.add_widget(Button(text="Back", on_press=self.go_back))
        self.nav_bar.add_widget(Button(text="Home", on_press=self.go_home))
        self.nav_bar.add_widget(Button(text="Refresh", on_press=self.refresh))
        self.nav_bar.opacity = 0
        self.add_widget(self.nav_bar)

    def go_back(self, instance=None):
        if hasattr(self, 'webview') and self.webview.canGoBack():
            self.webview.goBack()

    def go_forward(self):
        if hasattr(self, 'webview') and self.webview.canGoForward():
            self.webview.goForward()

    def go_home(self, instance=None):
        if hasattr(self, 'webview'):
            self.webview.loadUrl(self.url)

    def refresh(self, instance=None):
        if hasattr(self, 'webview'):
            self.webview.reload()

    def show_error(self, message):
        self.clear_widgets()
        self.add_widget(Label(text=message, font_size='20sp'))

    def on_touch_down(self, touch):
        self.start_x = touch.x
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        dx = touch.x - self.start_x
        if abs(dx) > 80:
            if dx > 0:
                self.go_back()
            else:
                self.go_forward()
        return super().on_touch_up(touch)

class MainApp(App):
    def build(self):
        self.main_layout = MainLayout()
        Clock.schedule_once(self.load_webview, 3)
        if platform == "android":
            activity.bind(on_new_intent=self.on_back_pressed)
        return self.main_layout

    @run_on_ui_thread
    def load_webview(self, dt):
        if platform == "android":
            try:
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                WebView = autoclass('android.webkit.WebView')
                WebViewClient = autoclass('android.webkit.WebViewClient')
                ConnectivityManager = autoclass('android.net.ConnectivityManager')
                Context = autoclass('android.content.Context')

                activity_instance = PythonActivity.mActivity
                conn_service = cast(ConnectivityManager,
                    activity_instance.getSystemService(Context.CONNECTIVITY_SERVICE))
                net_info = conn_service.getActiveNetworkInfo()

                if net_info is not None and net_info.isConnected():
                    self.main_layout.clear_widgets()

                    self.main_layout.webview = WebView(activity_instance)
                    self.main_layout.webview.getSettings().setJavaScriptEnabled(True)
                    self.main_layout.webview.setWebViewClient(WebViewClient())
                    self.main_layout.webview.loadUrl(self.main_layout.url)
                    self.main_layout.webview.setOnKeyListener(self.get_key_listener())

                    vertical_layout = BoxLayout(orientation='vertical')
                    vertical_layout.add_widget(self.main_layout.webview)
                    vertical_layout.add_widget(self.main_layout.nav_bar)
                    activity_instance.setContentView(vertical_layout)

                    self.main_layout.nav_bar.opacity = 1

                else:
                    self.main_layout.show_error("No Internet Connection")

            except Exception as e:
                self.main_layout.show_error("Error: " + str(e))

    def get_key_listener(self):
        OnKeyListener = autoclass('android.view.View$OnKeyListener')
        KeyEvent = autoclass('android.view.KeyEvent')

        class MyKeyListener(OnKeyListener):
            def __init__(self, outer):
                self.outer = outer

            def onKey(self, v, keyCode, event):
                if keyCode == KeyEvent.KEYCODE_BACK and self.outer.main_layout.webview.canGoBack():
                    self.outer.main_layout.webview.goBack()
                    return True
                return False

        return MyKeyListener(self)

    def on_back_pressed(self, *args):
        if hasattr(self.main_layout, 'webview') and self.main_layout.webview.canGoBack():
            self.main_layout.webview.goBack()

if __name__ == "__main__":
    MainApp().run()
