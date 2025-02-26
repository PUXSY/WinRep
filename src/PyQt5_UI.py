import sys
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QApplication, QStackedWidget, QMessageBox
from PyQt5.QtGui import QIcon
from pathlib import Path    
from logger import Logger

log = Logger()

class UIConfig:
    WINDOW_HEIGHT = 570
    WINDOW_WIDTH = 1170
    WINDOW_TITLE = "WinRep"
    WINDOW_ICON = Path(__file__).parent / "../assets/WinRep.png"
    
    PATHS = {
        'main': Path(__file__).parent / "../assets/MainWindow.ui",
        'basic': Path(__file__).parent / "../assets/BasicWindow.ui",
        'gaming': Path(__file__).parent / "../assets/GamingWindow.ui",
        'professional': Path(__file__).parent / "../assets/ProfessionalWindow.ui",
        'info': Path(__file__).parent / "../assets/InfoWindow.ui"
    }

class BaseWindow(QDialog):
    def __init__(self, ui_path, app_instance=None):
        super().__init__()
        self.app_instance = app_instance
        loadUi(str(ui_path), self)
        
    def setup_button(self, button_name, callback):
        button = self.findChild((QtWidgets.QPushButton, QtWidgets.QToolButton), button_name)
        if button:
            button.clicked.connect(callback)
        else:
            log.log_error(f"QPushButton '{button_name}' not found in UI file")
            
    def setup_ok_button(self, callback):
        button_name = f"{self.__class__.__name__.replace('Window', '')}_OK"
        ok_button = self.findChild(QtWidgets.QPushButton, button_name)
        if ok_button:
            ok_button.clicked.connect(callback)
        else:
            log.log_error("OK button not found in UI file")

class MainWindow(BaseWindow):
    def __init__(self, app_instance=None):
        super().__init__(UIConfig.PATHS['main'], app_instance)
        self.setup_navigation()
        
    def setup_navigation(self):
        buttons = {
            'Basic_Butten': (self.go_to_basic, 1),
            'Gaming_Butten': (self.go_to_gaming, 2),
            'Professional_Butten': (self.go_to_professional, 3),
            'info_butten': (self.go_to_info, 4)
        }
        for button_name, (callback, _) in buttons.items():
            self.setup_button(button_name, callback)
    
    def go_to_basic(self): widget.setCurrentIndex(1)
    def go_to_gaming(self): widget.setCurrentIndex(2)
    def go_to_professional(self): widget.setCurrentIndex(3)
    def go_to_info(self): widget.setCurrentIndex(4)

class SubWindow(BaseWindow):
    def __init__(self, ui_path, app_instance=None):
        super().__init__(ui_path, app_instance)
        self.setup_button('main_butten', self.go_to_main)
        self.setup_ok_button(self.handle_ok)

    def go_to_main(self):
        widget.setCurrentIndex(0)
        
    def handle_ok(self):
        preset_name = self.get_preset_name()
        if preset_name and self.app_instance:
            try:
                test_result = self.app_instance.run_preset_test(preset_name)
                if test_result is None:
                    QMessageBox.critical(self, "Error", f"Could not find or load preset file: {preset_name}")
                    return
                    
                if test_result:
                    try:
                        self.app_instance.run_preset(preset_name)
                        QMessageBox.information(self, "Success", f"Successfully applied {preset_name} preset!")
                    except Exception as e:
                        log.log_error(f"Error running preset: {str(e)}")
                        QMessageBox.critical(self, "Error", f"Error running preset: {str(e)}")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to test {preset_name} preset!")
            except Exception as e:
                log.log_error(f"Error applying preset: {str(e)}")
                QMessageBox.critical(self, "Error", f"Error applying preset: {str(e)}")
    
    def get_preset_name(self):
        names = {
            'BasicWindow': 'Basic.json',
            'GamingWindow': 'Gaming.json',
            'ProfessionalWindow': 'Professional.json',
        }
        print(names.get(self.__class__.__name__, None))
        return names.get(self.__class__.__name__, None)

class BasicWindow(SubWindow):
    def __init__(self, app_instance=None):
        super().__init__(UIConfig.PATHS['basic'], app_instance)

class GamingWindow(SubWindow):
    def __init__(self, app_instance=None):
        super().__init__(UIConfig.PATHS['gaming'], app_instance)

class ProfessionalWindow(SubWindow):
    def __init__(self, app_instance=None):
        super().__init__(UIConfig.PATHS['professional'], app_instance)

class InfoWindow(SubWindow):
    def __init__(self, app_instance=None):
        super().__init__(UIConfig.PATHS['info'], app_instance)

def setup_app(app_instance):
    app = QApplication(sys.argv)
    stack = QStackedWidget()
    
    windows = [
        MainWindow(app_instance),
        BasicWindow(app_instance),
        GamingWindow(app_instance),
        ProfessionalWindow(app_instance),
        InfoWindow(app_instance)
    ]
    
    for window in windows:
        stack.addWidget(window)
        
    stack.setFixedHeight(UIConfig.WINDOW_HEIGHT)
    stack.setFixedWidth(UIConfig.WINDOW_WIDTH)
    stack.setWindowTitle(UIConfig.WINDOW_TITLE)
    
    icon_path = str(UIConfig.WINDOW_ICON)
    if Path(icon_path).exists():
        stack.setWindowIcon(QIcon(icon_path))
        app.setWindowIcon(QIcon(icon_path))
    else:
        log.log_error(f"Window icon not found at: {icon_path}")
    
    return app, stack

def run_app(app_instance):
    """Initialize and run the application."""
    global widget  
    app, widget = setup_app(app_instance)
    widget.show()
    
    try:
        return app.exec_()
    except Exception as e:
        log.log_error(f"Application crashed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(run_app(None))