import os
import re
from tkinter import *
from tkinter.ttk import *
import serial


def main():
    print('-----------------------------------------------')
    print("Observer's log helper reading digi birds depths")
    print('-----------------------------------------------')


    com_port_string = ""
    root = Tk()
    parent = Frame(root)
    root.title("DigiCourse Birds depths Excel helper")
    Label(parent, text="Please select COM port that is connected to DigiCourse PC:").pack()
    Label(parent, text="COM port:").pack(side="left")
    Combobox(parent, textvariable=com_port_string, values=["COM1", "COM2"]).pack(side="left")
    Button(parent, text="Connect").pack(side="left")

    parent.pack()
    status_frame = Frame(root)
    Label(status_frame, text="Status:").pack()
    Label(status_frame, text="Found:").pack()
    status_frame.pack()

    console_frame = Frame(root)
    text_console = Text(console_frame)
    text_console.pack()
    console_frame.pack()

    text_console.insert('1.0', display_bird_information())

    root.mainloop()


def read_file():
    data = '''Q12:04:380148505C020337C063293C102501C120390C1304130012BT01029803072658BT0202860
1992851BT03028002051497BT04031302272774BT05029802732619BT06030402442774BT0703510
2172387BT08034801932503BT09032101192735BT10026802082580BT12008302392812BT1300650
2441691'''
    pattern = re.compile(r'\s+')  # removes whitespaces inside the incoming string
    data = re.sub(pattern, '', data)
    return data


def open_serial_port_and_read():
    with serial.Serial('COM1', 9600, timeout=1) as ser:
        line = ser.readline()  # read a '\n' terminated line


def write_to_file(data_to_save):
    with open(os.path.join(os.path.abspath('.'), 'birds_data.txt'), 'w') as save_file:
        save_file.write(str(list(data_to_save.values())).strip('[]'))


def parse_bird_data():
    parsed_information = {}
    bird_data = read_file()

    single_line_regex = re.compile(r'BT\d{12}', re.DOTALL)
    raw_birds = single_line_regex.findall(bird_data)

    for bird in raw_birds:
        bird_number = bird[2:4]
        bird_depth = int(bird[4:8]) / 100
        parsed_information[bird_number] = bird_depth

    return parsed_information


def display_bird_information():
    print('Information about the received birds: ')
    data_to_save = parse_bird_data()
    write_to_file(data_to_save)
    print('Depths written to a file : ' + str(data_to_save))
    return str(data_to_save)


if __name__ == '__main__':
    main()
