from mysql.connector import connect, Error

from PyQt6 import QtWidgets, QtGui
from PyQt6.QtWidgets import  QWidget, QLabel, QVBoxLayout
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import QSize, Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QPixmap
import yaml, sys, cv2, numpy as np, pathlib, os

filepath=pathlib.Path(__file__).parent.resolve() #path of file accesed
####################################################################### MYSQL login

config_data = yaml.load(open(str(filepath)+r'\config.yml'), Loader=yaml.FullLoader)
try:
    conn = connect(host=config_data["host"],
        user=config_data["user"],
        passwd=config_data["passwd"],
        database=config_data["db"]
    )
    if conn.is_connected():
        db_Info = conn.get_server_info()
        print("Connected to MySQL Server version ", db_Info)
        cursor = conn.cursor()
        cursor.execute("select database();")
        record = cursor.fetchone()
        print("You're connected to database: ", record)

except Error as e:
    print("Error while connecting to MySQL", e)
######################################################################


#REAL SHIT lol
###################################################################### Face recognition
class face_recog(QThread):
    
    change_pixmap_signal = pyqtSignal(np.ndarray)
    def __init__(self, calledfrom):
        super().__init__()
        self._run_flag = True
        self.calledfrom = calledfrom
    
    def run(self): 

        if len(sys.argv) < 2:
            video_mode= 0
        else:
            video_mode = sys.argv[1] 

        cascasdepath = str(filepath)+r'\haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascasdepath)
        video_capture = cv2.VideoCapture(video_mode)
        path = str(filepath)+r'\face'
        while self._run_flag:
            ret, image = video_capture.read()
            if ret:
                faces = face_cascade.detectMultiScale( #actual face recog here
                image,
                scaleFactor = 1.2,
                minNeighbors = 5,
                minSize = (200,200)
                )
                count = 0
                for (x,y,w,h) in faces:
                    face = image[y:y+h, x:x+w] #slice the face from the image
                    cv2.rectangle(image, (x,y), (x+h, y+h), (0, 255, 0), 2)
                    if count <2:
                        if (self.calledfrom=='accountcreate'): #functionality changes based on which method facerecog is called from
                            cv2.imwrite(os.path.join(path, str(count)+'.jpg'), face)
                        if (self.calledfrom=='compare'):
                            print(filepath)

                self.change_pixmap_signal.emit(image)
        

        video_capture.release()

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()
######################################################################        

###################################################################### Main login 
class Login(QtWidgets.QWidget): #login checks for username first, then goes to face compare 
    def __init__(self):
        super().__init__()

        self.setMinimumSize(QSize(400, 200)) #lol

        self.Username = QLabel(self) #setup label
        self.Username.setText("Username: ")
        self.UserEntry = QtWidgets.QLineEdit(self)
        self.Username.move(80, 20) 
        self.Username.resize(200, 32)
        self.UserEntry.move(150, 20)

        login = QPushButton('Login', self)
        login.clicked.connect(self.Login)
        login.resize(210,70)
        login.move(75, 60)

        createAcc = QPushButton('Create Account', self)
        self.w = None
        createAcc.clicked.connect(self.show_new_window)
        createAcc.resize(210,70)
        createAcc.move(75, 120)

    def show_new_window(self):
        self.hide()
        if self.w is None:
            self.w = accountCreation()
            self.w.show()

        else:
            self.w.close()  # Close window.
            self.w = None  # Discard reference.
  
    #login function     
    def Login(self):
        Username= self.UserEntry.text()
        cursor.execute('SELECT username FROM images')
        usernames = [row[0] for row in cursor.fetchall()]
        # Compare the string to each username in the list
        founduser=False
        for username in usernames:
            if Username == username:
                founduser=True
                break

        if founduser==True:
            self.hide()
            if self.w is None:
                self.w = FaceComaparison()
                self.w.show()
            else:
                self.w.close()  # Close window.
                self.w = None  # Discard reference.

######################################################################

class FaceComaparison(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(QSize(400, 200)) #lol
        self.setWindowTitle("face_recog")
        self.display_width=640
        self.display_height=480

        self.image_label=QLabel(self)
        self.image_label.resize(self.display_width, self.display_height)

        self.thread = face_recog(calledfrom='compare')
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.start()
        
    def closeEvent(self, event): #so face recog actually closes on program end 
        self.thread.stop()
        event.accept()

    @pyqtSlot(np.ndarray) #references change_pixmap_signal
    def update_image(self, image):
        qt_img = self.convert_cv_qt(image)
        self.image_label.setPixmap(qt_img)

    def convert_cv_qt(self, image): #all of the processing happens here
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape #all of this is to convert for pyqt6 usage
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.display_width, self.display_height, Qt.AspectRatioMode.KeepAspectRatio)
        return QPixmap.fromImage(p)

        
###################################################################### New window to create an account
class accountCreation(QWidget): #to create account, probably going to use a lot of cv2
    def __init__(self):
        super().__init__()
        self.setMinimumSize(QSize(400, 200)) #lol

        face_account = QPushButton("Face Recognition", self)
        self.w = None
        face_account.clicked.connect(self.show_face_recog)
        face_account.resize(210,70)
        face_account.move(75, 0)

        Exit = QPushButton('Exit', self)
        Exit.clicked.connect(self.show_new_window)
        self.Login = Login()
        Exit.resize(210,70)
        Exit.move(75, 60)

    def show_face_recog(self):
        self.hide()
        if self.w is None:
            self.w = face_recog_holder()
            self.w.show()
        else:
            self.w.close()  # Close window.
            self.w = None  # Discard reference.

    def show_new_window(self):
        self.hide()
        self.Login.show()

######################################################################

###################################################################### PyQt6 window to hold cv2 face recog
class face_recog_holder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("face_recog")
        self.display_width=640
        self.display_height=480

        self.image_label=QLabel(self)
        self.image_label.resize(self.display_width, self.display_height)

        self.Username = QLabel(self) #setup label
        self.Username.setText("Username: ")
        self.UserEntry = QtWidgets.QLineEdit(self)
        self.Username.move(80, 20) 
        self.Username.resize(200, 32)
        self.UserEntry.move(150, 20)

        self.allGood = QLabel(self)
        self.allGood.setText("Face found, you can exit")
        self.allGood.move(70, 0)


        Exit = QPushButton("Exit", self)
        self.w = None
        Exit.clicked.connect(self.show_accountCreation)
        Exit.resize(210,70)
        Exit.move(75, 0)

        vbox = QVBoxLayout()
        vbox.addWidget(self.image_label)
        vbox.addWidget(Exit)
        self.setLayout(vbox)

        self.thread = face_recog(calledfrom='accountcreate')
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.start()

    def show_accountCreation(self):
        new_username = self.UserEntry.text()
        cursor.execute('SELECT username FROM images')
        usernames = [row[0] for row in cursor.fetchall()]
        # Compare the string to each username in the list
        useralrexists=False
        for username in usernames:
            if new_username == username:
                self.allGood.setText("Username Already Exists")
                useralrexists=True
                break
        if useralrexists==False:
            self.hide()
            cursor.execute("SELECT MAX(id) FROM images")
            max_id=cursor.fetchone()[0]
            add_row = ("INSERT INTO images "
            "(id, username, face) "
            "VALUES (%s, %s, %s)")
            if max_id is None:
                new_id = 1
            else:
                new_id = max_id + 1
            
            new_face = open(str(filepath)+r'\face\0.jpg', 'rb').read() #rb is read binary
            cursor.execute(add_row, (new_id, new_username, new_face))
            conn.commit()
            if self.w is None:
                self.w = accountCreation()
                self.w.show()
                self.thread.stop() #so i dont get fucked wih errors
                #cursor._batch_insert
            else:
                self.w.close()  # Close window.
                self.w = None  # Discard reference

    def closeEvent(self, event): #so face recog actually closes on program end 
        self.thread.stop()
        event.accept()

    @pyqtSlot(np.ndarray) #references change_pixmap_signal
    def update_image(self, image):
        qt_img = self.convert_cv_qt(image)
        self.image_label.setPixmap(qt_img)

    def convert_cv_qt(self, image): #all of the processing happens here
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape #all of this is to convert for pyqt6 usage
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.display_width, self.display_height, Qt.AspectRatioMode.KeepAspectRatio)
        return QPixmap.fromImage(p)
######################################################################

#so nothing goes wrong
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mainWin = Login()
    mainWin.show()
    
    sys.exit( app.exec() )
    
 