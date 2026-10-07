#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2014 Paul Kinsella <kali.gsm.rtl.sdr@gmail.com>
# 
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.

import serial
import serial.tools.list_ports
import time
import sys
import glob

###################################
#   Serial setup
###################################
ser = serial.Serial()
ser.port = "COM4"  # default port
ser.baudrate = 9600
ser.bytesize = serial.EIGHTBITS
ser.parity = serial.PARITY_NONE
ser.stopbits = serial.STOPBITS_ONE
ser.timeout = 0             # non-blocking read
ser.xonxoff = False
ser.rtscts = False
ser.dsrdtr = False

# Character sets untuk GSM 7-bit default alphabet & extension
gsm = ("@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ\x1bÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?"
       "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ`¿abcdefghijklmnopqrstuvwxyzäöñüà")
ext = ("````````````````````^```````````````````{}`````\\````````````[~]`"
       "|````````````````````````````````````€``````````````````````````")

#################################
# Return serial ports list
#################################
def getOpenSerialPorts():
    """
    Mendeteksi daftar port serial yang tersedia di Windows (COM1-COM256) 
    maupun Linux/macOS secara otomatis.
    """
    result = []
    
    # Pendekatan 1: Menggunakan pustaka PySerial (Rekomendasi Utama Cross-Platform)
    ports = serial.tools.list_ports.comports()
    for p in ports:
        result.append(p.device)
        
    # Pendekatan 2: Fallback scan manual jika berjalan di Windows & list_ports kosong
    if not result and sys.platform.startswith('win'):
        for i in range(1, 256):
            port_name = f"COM{i}"
            try:
                s = serial.Serial(port_name)
                s.close()
                result.append(port_name)
            except (serial.SerialException, OSError):
                pass

    # Pendekatan 3: Fallback khusus Linux jika dijalankan di sistem POSIX
    elif not result and sys.platform.startswith('linux'):
        temp_list = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyS*')
        for a_port in temp_list:
            try:
                s = serial.Serial(a_port)
                s.close()
                result.append(a_port)
            except (serial.SerialException, OSError):
                pass

    return result

########################################################################
#   GET BACK AN AT COMMAND REPLY
########################################################################
def getAtReply(serial_port, at_command):
    ser.port = serial_port
    if not ser.isOpen():
        ser.open()
    time.sleep(0.3)
    ress = ""
    if ser.isOpen():
        ser.flushInput()   # flush input buffer
        ser.flushOutput()  # flush output buffer
        sercmd = at_command
        ser.write((sercmd + "\r").encode())
        time.sleep(0.2)
        bytesToRead = ser.inWaiting()
        ress = ser.read(bytesToRead).decode(errors='ignore')
        ser.close()
    return ress

###############################################################################
#   SWAPS NUMBER EVERY 2 DIGITS USED FOR PDU
#############################################################################
def swapNumber(number):
    swaparray = []
    returnNumber = ""
    first1, first2 = 0, 1
    second1, second2 = 1, 2

    for x in range(0, len(number) // 2):
        swaparray.append(number[second1:second2])
        swaparray.append(number[first1:first2])
        first1 += 2
        first2 += 2
        second1 += 2
        second2 += 2

    for num in swaparray:
        returnNumber += num
    return returnNumber 

###############################################################################
#   ENCODE SMS TEXT TO GSM
#############################################################################
def gsm_encode(plaintext):
    res = bytearray()
    for c in plaintext:
        idx = gsm.find(c)
        if idx != -1:
            res.append(idx)
            continue
        idx = ext.find(c)
        if idx != -1:
            res.append(27)
            res.append(idx)

    return res.hex().upper()

###############################################################################
#   ENCODE SMS TEXT TO GSM 8bit
#############################################################################
def gsm_encode8bit(SMS):
    return gsm_encode(SMS)

###############################################################################
#   STRING TO HEX
#############################################################################
def stringToHex(str2hex):
    return str2hex.encode('utf-8').hex().upper()

###############################################################################
#   STRING TO HEX 16/18 bit UCS2 Style
#############################################################################
def stringToHex18bit(str2hex):
    hexbuffer = ""
    for c in str2hex:
        hexbuffer += f"00{c.encode('utf-8').hex()}"
    return hexbuffer.upper()

########################################################################
#           CREATE PDU STRING
########################################################################
def createPduString(phone_num, sms_text, message_type, del_report_status):
    NUMBER_LEN = len(phone_num)
    NUMBER = phone_num
    SMS_TYPE = message_type

    # Jika nomor ganjil, tambahkan 'F' agar genap
    if NUMBER_LEN % 2 != 0:
        NUMBER += "F"

    NUMBER = swapNumber(NUMBER)
    NUMBER_LEN_HEX = f"{NUMBER_LEN:02X}"

    smslen = len(sms_text) * 2
    MSG_LEN_HEX = f"{smslen:02X}"

    DEL_REPORT = "21" if del_report_status else "01"
    decodedstr1 = stringToHex18bit(sms_text)

    PDU_STRING = f"00{DEL_REPORT}00{NUMBER_LEN_HEX}91{NUMBER}00{SMS_TYPE}{MSG_LEN_HEX}{decodedstr1}"

    return PDU_STRING

########################################################################
#           CREATE WAP PUSH PDU STRING
########################################################################
def createWapPduString(start_date, end_date, header, target_num, msg, wap_type):
    NUMBER = target_num 
    NUMBER_LEN = len(target_num)
    NUMBER_LEN_HEX = f"{NUMBER_LEN:02X}"
    
    if NUMBER_LEN % 2 != 0:
        NUMBER += "F"

    NUMBER = swapNumber(NUMBER)

    smslen = len(msg) + 69
    MSG_LEN_HEX = f"{smslen:02X}"

    WAP_PDU_STRING = (
        f"004100{NUMBER_LEN_HEX}91{NUMBER}0004{MSG_LEN_HEX}"
        f"0B05040B84C0020003F001010B060403AE81EA02056A0045C6{wap_type}"
        f"03{stringToHex(header)}000AC306{start_date}10C306{end_date}0103{stringToHex(msg)}000101"
    )

    return WAP_PDU_STRING