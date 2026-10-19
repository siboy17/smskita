#!/usr/bin/env python

# Copyright 2015 Paul Kinsella <kali.gsm.rtl.sdr@gmail.com>
# 
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.

import wx
import serial
import time
from smsfuzzer_funcs import * 

# Inisialisasi Serial Port Default
mySerialPort = serial.Serial()
mySerialPort.port = "/dev/ttyUSB0"
mySerialPort.baudrate = 9600
mySerialPort.bytesize = serial.EIGHTBITS
mySerialPort.parity = serial.PARITY_NONE
mySerialPort.stopbits = serial.STOPBITS_ONE
mySerialPort.timeout = 0
mySerialPort.xonxoff = False
mySerialPort.rtscts = False
mySerialPort.dsrdtr = False

FLASH1 = "10"  # 4 bit encoding
FLASH2 = "14"  # 8 bit encoding
FLASH3 = "18"
SILENT = "C0"
NORMAL = "08"


class ExampleFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, size=(240, 230), title='Sms Fuzzer')
        panel = wx.Panel(self)

        # Mendapatkan daftar serial port
        tested_ports = getOpenSerialPorts()
        if len(tested_ports) < 1:
            tested_ports.append("NO PORTS")

        # Layout UI
        self.lb_comport = wx.StaticText(panel, label="Com Port:", pos=(5, 5))
        self.combo_serial_ports = wx.ComboBox(panel, size=(135, 30), pos=(80, 5), choices=tested_ports, style=wx.CB_READONLY)
        self.combo_serial_ports.SetSelection(0)

        self.lb_smstype = wx.StaticText(panel, label="Sms Type:", pos=(5, 35))
        self.combo_sms_type = wx.ComboBox(panel, size=(135, 30), pos=(80, 35), choices=['NORMAL', 'FLASH', 'SILENT'], style=wx.CB_READONLY)
        self.combo_sms_type.SetSelection(0)

        self.lb_target = wx.StaticText(panel, label="Target No:", pos=(5, 65))
        self.edit_target_number = wx.TextCtrl(panel, size=(135, 30), pos=(80, 65), value='6282179003599')

        self.lb_target_data = wx.StaticText(panel, label="Sms Msg:", pos=(5, 95))
        self.edit_target_msg = wx.TextCtrl(panel, size=(135, 50), pos=(80, 95), value='Hello World', style=wx.TE_MULTILINE)

        self.cb_report = wx.CheckBox(panel, -1, 'Del\nReport', pos=(5, 110), size=(80, 50))
        self.cb_report.SetValue(True)

        self.btnpdumode = wx.Button(panel, label="Pdu Mode", pos=(5, 155), size=(75, 25))
        self.btnpdumode.Bind(wx.EVT_BUTTON, self.onPduModeClick)

        self.btn2g_mode = wx.Button(panel, label="2G Mode", pos=(85, 155), size=(70, 25))
        self.btn2g_mode.Bind(wx.EVT_BUTTON, self.on2gModeClick)

        self.btnsend = wx.Button(panel, label="Send", pos=(160, 155), size=(55, 25))
        self.btnsend.Bind(wx.EVT_BUTTON, self.onSendClick)

        self.lb_output = wx.StaticText(panel, label="Debug:", pos=(5, 185))

    # Event Handlers sebagai metode kelas
    def onPduModeClick(self, event):
        reply = getAtReply(self.combo_serial_ports.GetValue(), "AT+CMGF=0")
        wx.MessageBox(str(reply), 'Info', wx.OK | wx.ICON_INFORMATION)

    def on2gModeClick(self, event):
        reply = getAtReply(self.combo_serial_ports.GetValue(), "AT^SYSCFG=13,1,3FFFFFFF,2,4")
        wx.MessageBox(str(reply), 'Info', wx.OK | wx.ICON_INFORMATION)

    def onSendClick(self, event):
        mySerialPort.port = self.combo_serial_ports.GetValue()
        DEL_REPORT_STATUS = self.cb_report.GetValue()

        smstype = self.combo_sms_type.GetValue()
        SMS_TYPE = NORMAL
        if smstype == "SILENT":
            SMS_TYPE = SILENT
        elif smstype == "FLASH":
            SMS_TYPE = FLASH3

        try:
            if not mySerialPort.isOpen():
                mySerialPort.open()

            if mySerialPort.isOpen():
                mySerialPort.flushInput()
                mySerialPort.flushOutput()

                # Buat string PDU
                PDU_STRING = createPduString(
                    self.edit_target_number.GetValue(),
                    self.edit_target_msg.GetValue(),
                    SMS_TYPE, 
                    DEL_REPORT_STATUS
                )

                # Hitung panjang octet TPDU (mengabaikan SMSC header 00 di depan)
                # Jika PDU_STRING diawali '00', panjang TPDU dalam octet = (len(PDU) - 2) // 2
                pdu_len = (len(PDU_STRING) - 2) // 2 if PDU_STRING.startswith("00") else len(PDU_STRING) // 2

                # Kirim perintah AT+CMGS
                mySerialPort.write(f"AT+CMGS={pdu_len}\r".encode())
                time.sleep(0.3)

                # Kirim PDU string diakhiri Ctrl+Z (\x1A)
                mySerialPort.write((PDU_STRING + "\x1A").encode())
                time.sleep(0.5)

                bytesToRead = mySerialPort.inWaiting()
                ress = mySerialPort.read(bytesToRead).decode(errors='ignore')
                wx.MessageBox(ress if ress else "Sent (No response)", 'Info', wx.OK | wx.ICON_INFORMATION)
            else:
                wx.MessageBox('Message did not send (Port closed)', 'Info', wx.OK | wx.ICON_INFORMATION)

        except Exception as e:
            wx.MessageBox(f"Error: {str(e)}", 'Error', wx.OK | wx.ICON_ERROR)
        finally:
            if mySerialPort.isOpen():
                mySerialPort.close()


if __name__ == '__main__':
    app = wx.App(False)
    frame = ExampleFrame(None)
    frame.Show()
    app.MainLoop()
