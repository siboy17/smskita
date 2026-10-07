#!/usr/bin/env python

import time
import serial
import wx

# Pastikan module smsfuzzer_funcs ada di direktori yang sama
from smsfuzzer_funcs import * 

# Inisialisasi konfigurasi Serial Port
mySerialPort = serial.Serial()
mySerialPort.port = "COM4"  # default port
mySerialPort.baudrate = 9600
mySerialPort.bytesize = serial.EIGHTBITS
mySerialPort.parity = serial.PARITY_NONE
mySerialPort.stopbits = serial.STOPBITS_ONE
mySerialPort.timeout = 0  # non-blocking read
mySerialPort.xonxoff = False
mySerialPort.rtscts = False
mySerialPort.dsrdtr = False

WAP_TYPE = [
    "01", "02", "03", "04", "05", "06", "07", "08",
    "09", "0A", "0B", "0C", "0D", "0E", "0F"
]

class ExampleFrame(wx.Frame):
    def __init__(self, parent):
        # Memperbesar ukuran frame agar layout tidak terpotong
        wx.Frame.__init__(self, parent, size=(240, 400), title='Wap Push')
        panel = wx.Panel(self)

        # Mendapatkan daftar serial port yang tersedia
        tested_ports = getOpenSerialPorts()
        if len(tested_ports) < 1:
            tested_ports.append("NO PORTS")

        # --- UI CONTROLS ---
        self.lb_comport = wx.StaticText(panel, label="Com Port:", pos=(5, 5))
        self.combo_serial_ports = wx.ComboBox(
            panel, size=(135, 30), pos=(80, 5), 
            choices=tested_ports, style=wx.CB_READONLY
        )
        self.combo_serial_ports.SetSelection(0)

        self.lb_start_date = wx.StaticText(panel, label="Start Date:", pos=(5, 35))
        self.edit_start_date = wx.TextCtrl(panel, size=(135, 30), pos=(80, 35), value='201502012221')

        self.lb_end_date = wx.StaticText(panel, label="End Date:", pos=(5, 65))
        self.edit_end_date = wx.TextCtrl(panel, size=(135, 30), pos=(80, 65), value='201502212230')

        self.lb_header = wx.StaticText(panel, label="Header:", pos=(5, 95))
        self.edit_header = wx.TextCtrl(panel, size=(135, 30), pos=(80, 95), value='www.headerhere.com')

        self.lb_target = wx.StaticText(panel, label="Target No:", pos=(5, 125))
        self.edit_target_number = wx.TextCtrl(panel, size=(135, 30), pos=(80, 125), value='123456789012')

        self.lb_target_data = wx.StaticText(panel, label="Sms Msg:", pos=(5, 155))
        self.edit_target_msg = wx.TextCtrl(
            panel, size=(135, 50), pos=(80, 155), 
            value='Hello World', style=wx.TE_MULTILINE
        )

        self.btnpdumode = wx.Button(panel, label="Pdu Mode", pos=(5, 215), size=(80, 30))
        self.combo_wap_types = wx.ComboBox(
            panel, pos=(90, 215), size=(65, 30), 
            choices=WAP_TYPE, style=wx.CB_READONLY
        )
        self.combo_wap_types.SetSelection(11)

        self.btnsend = wx.Button(panel, label="Send", pos=(160, 215), size=(60, 30))

        self.lb_output = wx.StaticText(panel, label="Debug:", pos=(5, 250))
        self.edit_debug = wx.TextCtrl(
            panel, size=(215, 80), pos=(5, 270), 
            value='', style=wx.TE_MULTILINE
        )

        # --- EVENT BINDINGS ---
        self.btnpdumode.Bind(wx.EVT_BUTTON, self.onPduModeClick)
        self.btnsend.Bind(wx.EVT_BUTTON, self.onSendClick)

    def onPduModeClick(self, event):
        port_name = self.combo_serial_ports.GetValue()
        reply = getAtReply(port_name, "AT+CMGF=0")
        wx.MessageBox(str(reply), 'Info', wx.OK | wx.ICON_INFORMATION)

    def onSendClick(self, event):
        mySerialPort.port = self.combo_serial_ports.GetValue()
        
        WAP_PDU_STRING = createWapPduString(
            self.edit_start_date.GetValue(),
            self.edit_end_date.GetValue(),
            self.edit_header.GetValue(),
            self.edit_target_number.GetValue(),
            self.edit_target_msg.GetValue(),
            self.combo_wap_types.GetValue()
        )

        self.edit_debug.SetValue(WAP_PDU_STRING)

        try:
            if not mySerialPort.is_open:
                mySerialPort.open()

            if mySerialPort.is_open:
                mySerialPort.reset_input_buffer()
                mySerialPort.reset_output_buffer()
                
                # Kirim perintah AT
                mySerialPort.write(b"AT+CMGS=17\r")
                time.sleep(0.3)
                
                # Kirim string PDU dan karakter Ctrl+Z (\x1A)
                mySerialPort.write(WAP_PDU_STRING.encode('utf-8') + b"\x1A")
                time.sleep(0.3)
                
                bytesToRead = mySerialPort.in_waiting
                ress = mySerialPort.read(bytesToRead).decode('utf-8', errors='ignore')
                
                wx.MessageBox(ress, 'Info', wx.OK | wx.ICON_INFORMATION)
            else:
                wx.MessageBox('Message did not send', 'Info', wx.OK | wx.ICON_INFORMATION)

        except Exception as e:
            wx.MessageBox(f'Serial Error: {str(e)}', 'Error', wx.OK | wx.ICON_ERROR)
            
        finally:
            if mySerialPort.is_open:
                mySerialPort.close()


if __name__ == '__main__':
    app = wx.App(False)
    frame = ExampleFrame(None)
    frame.Show()
    app.MainLoop()