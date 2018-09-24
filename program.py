import os
import re
from tkinter import *
from tkinter.ttk import *
import serial
import serial.tools.list_ports
from datetime import datetime
import threading


class Application:

    def __init__(self, root):
        self.root = root
        self.root.title("DigiCourse Birds depths Excel helper")

        parent = Frame(self.root)  # new frame inside which all widgets reside
        self.combobox = Combobox(parent, values=self.read_available_com_ports())  # creating and initilising Combobox

        console_frame = Frame(self.root)
        self.text_console = Text(console_frame)
        self.text_console.pack()

        Label(parent, text="Please select COM port that is connected to DigiCourse PC:").pack()
        Label(parent, text="COM port:").pack(side="left")

        self.combobox.pack(side="left")
        self.combobox.current(0)  # sets the first index as a selected option

        self.connect_button = Button(parent, text="Connect", command=self.button_pressed)
        self.connect_button.pack(side="left")

        parent.pack()
        status_frame = Frame(self.root)
        Label(status_frame, text="Status:").pack()
        Label(status_frame, text="Found:").pack()

        status_frame.pack()
        console_frame.pack()

        # text_console.insert('1.0', self.display_bird_information())

    def toggle_connect_button_state(self):
        if self.connect_button.cget("text") == 'Connect':
            self.connect_button.config(text="Connected")
        else:
            self.connect_button.config(text="Connect")

    def read_available_com_ports(self):
        # Creates a list with available COM ports using list comprehension
        return [comport.device for comport in serial.tools.list_ports.comports()]

    def button_pressed(self):
        self.open_serial_port_and_read_thread()

    # def read_file(self):
    #     data = '''Q12:04:380148505C020337C063293C102501C120390C1304130012BT01029803072658BT0202860
    # 1992851BT03028002051497BT04031302272774BT05029802732619BT06030402442774BT0703510
    # 2172387BT08034801932503BT09032101192735BT10026802082580BT12008302392812BT1300650
    # 2441691'''
    #     pattern = re.compile(r'\s+')  # removes whitespaces inside the incoming string
    #     data = re.sub(pattern, '', data)
    #     return data

    def open_serial_port_and_read(self):
        with serial.Serial(self.combobox.get(), 9600, timeout=1) as ser:
            while True:
                self.toggle_connect_button_state()
                line = ser.readline()  # read a '\n' terminated line
                data = str(line)
                if '-' in data:
                    self.text_console.insert('1.0',
                                             'String incorrect. Possible cause - DigiBirds in sleep mode\n')
                    return
                if 'Q' in data:
                    data_to_save = self.parse_bird_data(data)  # extracts depths and returns a dictionary data type
                    self.write_to_file(data_to_save)
                    self.text_console.insert('1.0',
                                             'Data saved at {} \n'.format(datetime.now().isoformat(timespec='seconds')) + str(
                                                 data_to_save))
                else:
                    self.text_console.insert('1.0',
                                             'Found incorrect or no data: {} \n'.format(data))
                    return

    def open_serial_port_and_read_thread(self):
        """
        A threading version of the open serial and read method
        """
        self.thread = threading.Thread(target=self.open_serial_port_and_read())
        self.thread.start()

    def write_to_file(self, data_to_save):
        with open(os.path.join(os.path.abspath('.'), 'digiBirdsDepthsLog.txt'), 'w') as save_file:
            save_file.write(str(list(data_to_save.values())).strip('[]'))

    def parse_bird_data(self, bird_data):
        parsed_information = {}

        single_line_regex = re.compile(r'BT\d{12}', re.DOTALL)
        raw_birds = single_line_regex.findall(bird_data)

        for bird in raw_birds:
            bird_number = bird[2:4]
            bird_depth = int(bird[4:8]) / 100
            parsed_information[bird_number] = bird_depth

        return parsed_information

    def display_bird_information(self):
        print('Information about the received birds: ')
        data_to_save = self.parse_bird_data()
        self.write_to_file(data_to_save)
        print('Depths written to a file : ' + str(data_to_save))
        return str(data_to_save)


if __name__ == '__main__':
    main_root = Tk()
    app = Application(main_root)
    main_root.mainloop()
