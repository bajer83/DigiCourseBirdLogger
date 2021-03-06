import os
import re
from tkinter import *
from tkinter.ttk import *
import serial
import serial.tools.list_ports
from datetime import datetime
import threading
import time


class Application:

    def __init__(self, root):
        self.root = root
        self.root.title("DigiCourse Birds depths Excel helper")

        # parent = Frame(self.root)  # new frame inside which all widgets reside

        Label(root, text="COM port:").grid(row=0, column=0, sticky=E)

        self.combobox = Combobox(root, values=self.read_available_com_ports())  # creating and initilising Combobox
        self.combobox.grid(row=0, column=1)
        # TODO Add a check for number of COM ports detected. If none the program will currently crash.
        self.combobox.current(0)  # sets the first index as a selected option

        self.connect_button = Button(root, text="Connect", command=self.connect_disconnect_event)
        self.connect_button.grid(row=0, column=2, columnspan=1, sticky=NSEW)

        Separator(root, orient='horizontal').grid(row=2, column=0, columnspan=3, sticky=NSEW, pady=[10, 0])

        Label(root, text="Status:").grid(row=3, column=0, sticky=W)
        self.status_label = Label(root, text="Not connected")
        self.status_label.grid(row=3, column=1, sticky=W)

        Label(root, text="Found:").grid(row=4, column=0, sticky=W)
        self.found_label = Label(root, text="0")
        self.found_label.grid(row=4, column=1, sticky=W)

        self.text_console = Text(self.root, width=50, height=5)
        self.text_console.grid(row=5, column=0, columnspan=3)
        Label(root, text='Powered by: Woj', font=('', 5)).grid(row=6, column=2, sticky=E)

        self.stop_thread = threading.Event()  # must contain brackets, this is the Even object that acts like a flag for a main while loop

        self.scroll_bar = Scrollbar(self.root)
        self.text_console.configure(yscrollcommand=self.scroll_bar.set)
        self.scroll_bar.config(command=self.text_console.yview)
        #
        self.scroll_bar.grid(row=5, column=4, sticky='NSW')

    def read_available_com_ports(self):
        # Creates a list with available COM ports using list comprehension
        return [comport.device for comport in serial.tools.list_ports.comports()]

    # def read_file(self):
    #     data = '''Q12:04:380148505C020337C063293C102501C120390C1304130012BT01029803072658BT0202860
    # 1992851BT03028002051497BT04031302272774BT05029802732619BT06030402442774BT0703510
    # 2172387BT08034801932503BT09032101192735BT10026802082580BT12008302392812BT1300650
    # 2441691'''
    #     pattern = re.compile(r'\s+')  # removes whitespaces inside the incoming string
    #     data = re.sub(pattern, '', data)
    #     return data

    def connect_disconnect_event(self):
        """
        Method that connects and diconnects from the selected COM port
        """
        if self.check_if_port_open():
            print("Port is Closed")
            self.connect_disconnect_event_thread()  # start a new thread that read serial data in a loop
            self.connect_button.config(text="Disconnect")
        else:
            print("Port is Opened")
            self.stop_thread.set()
            self.connect_button.config(text="Connect")

    def check_if_port_open(self):
        try:
            ser = serial.Serial(self.combobox.get(), 9600, timeout=0)
            ser.close()
            if not ser.is_open:
                return True
        except serial.SerialException as ex:
            return False

    def open_serial_port_and_read(self, stop_event, arg):

        with serial.Serial(self.combobox.get(), 9600, timeout=0) as ser:
            self.status_label.config(text="Connected")
            while not stop_event.is_set():  # the condition is set when the port status is checked.

                line = ser.readline()  # read a '\n' terminated line
                data = str(line)
                # if '-' in data:
                #    self.text_console.insert('1.0',
                #                            'String incorrect. Possible cause - DigiBirds in sleep mode\n')

                if 'Q' in data:
                    print('Passed data to save' + str(data))
                    data_to_save_tuple = self.parse_bird_data(
                        data)  # extracts depths and returns a dictionary data type
                    data_to_save, data_for_found = data_to_save_tuple  # unpacking tuple to two variables

                    self.found_label.config(text='Total number of birds: {} including {} compass birds'.format(
                        data_for_found['normal_number'],
                        data_for_found['compass_number']))

                    self.write_to_file(data_to_save)

                    self.text_console.delete('1.0', END)
                    self.text_console.insert('1.0',
                                             'Data saved at {} \n'.format(
                                                 datetime.now().isoformat(timespec='seconds')) + str(
                                                 data_to_save))

                else:
                    self.text_console.insert('1.0',
                                             'Found incorrect or no data: {} \n'.format(data))

                if self.count_lines_on_text_console() > 20:
                    self.text_console.delete("1.0", "20.0")
                    self.text_console.edit_reset()
                time.sleep(1)

        self.stop_thread.clear()  # sets the Event to False again so next time the button is pressed the while loop can start again
        self.status_label.config(text="Not connected")
        self.found_label.config(text="0")

    def count_lines_on_text_console(self):
        (line, c) = map(int, self.text_console.index("end-1c").split("."))
        return line

    def connect_disconnect_event_thread(self):
        """
        A threading version of the open serial and read method
        """
        thread = threading.Thread(target=self.open_serial_port_and_read, args=(self.stop_thread, "Serial thread"),
                                  daemon=TRUE)
        thread.start()

    def write_to_file(self, data_to_save):
        with open(os.path.join(os.path.abspath('.'), 'digiBirdsDepthsLog.txt'), 'w') as save_file:
            save_file.write(str(list(data_to_save.values())).strip('[]'))

    def parse_bird_data(self, bird_data):
        parsed_information = {}
        parsed_found_information = {"compass_number": 0, "normal_number": 0}
        print('Bird data before matching: ' + str(bird_data))
        single_line_regex = re.compile(r'BT[\d-]{12}', re.DOTALL | re.IGNORECASE)
        raw_birds = single_line_regex.findall(bird_data)

        print('Raw birds: ' + str(raw_birds))
        index = 0
        for bird in raw_birds:
            index += 1
            bird_number = bird[2:4]
            bird_depth = int(bird[4:8]) / 100
            parsed_information[bird_number] = bird_depth
            parsed_found_information['normal_number'] = index

        single_line_regex = re.compile(r'C\d{2}', re.DOTALL | re.IGNORECASE)
        compass_birds = single_line_regex.findall(bird_data)
        parsed_found_information['compass_number'] = len(compass_birds)

        return parsed_information, parsed_found_information

    def display_bird_information(self):
        print('Information about the received birds: ')
        data_to_save = self.parse_bird_data()
        self.write_to_file(data_to_save)
        print('Depths written to a file : ' + str(data_to_save))
        return str(data_to_save)


if __name__ == '__main__':
    main_root = Tk()
    # main_root.resizable(width=False, height=False)
    main_root.geometry('{}x{}'.format(430, 200))
    app = Application(main_root)
    main_root.mainloop()
