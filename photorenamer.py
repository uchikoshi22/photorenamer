#!/usr/bin/env python

import os
import sys
import csv
import shutil
import pyexiv2
import datetime

CONF_FILE_NAME = "renamer.conf"
DB_FILE_NAME = "renamer_db"
ERROR_FILE = "error.csv"

DIR_TYPE = {"S": "Source", "R": "Repository"}
FILE_TYPE = ["JPG", "jpg", "PNG", "png", "JPEG", "jpeg"]

class _Configuration:
    def __init__(self):
        self.conf_file = None
        self.conf_dir = None
        self.db_file = None
        self.db_dir = None
        self.source_dir = None
        self.repository_dir = None
        self.file_type = []
        self.conf_data = []

    def set_param(self, c_file, db_file, w_dir, src_dir, rep_dir, f_type, err_file):
        self.conf_file = c_file
        self.conf_dir = w_dir
        self.db_file = db_file
        self.db_dir = w_dir
        self.source_dir = src_dir
        self.repository_dir = rep_dir
        self.file_type = f_type[:]
        self.error_file = err_file

        self.conf_data = [ ["conf_file", self.conf_file],
                           ["conf_dir", self.conf_dir],
                           ["db_file", self.db_file],
                           ["db_dir", self.db_dir],
                           ["source_dir", self.source_dir],
                           ["repository_dir", self.repository_dir],
                           ["file_type", self.file_type],
                           ["error_file", self.error_file],
                           ]


    def write_conf(self):
        conf_path = os.path.join(self.conf_dir, self.conf_file)
        try:
            writer = csv.writer(file(conf_path, 'w'))
            for data in self.conf_data:
                writer.writerow(data)
        except:
            print "Error occured while the configuration file is being created"

    def init_db(self):
        db_path = os.path.join(self.db_dir, self.db_file)
        try:
            dbfile = open(db_path,'w')
            dbfile.close()
        except:
            print "Error occured while the db file is being created"

    def get_param_list(self, conf_file, conf_dir):
        os.chdir(conf_dir)
        param_list = []
        reader = csv.reader(file(conf_file, 'r'))

        for param in reader:
            param_list.append(param)

        self.set_param(param_list[0][1],
                       param_list[2][1],
                       param_list[1][1],
                       param_list[4][1],
                       param_list[5][1],
                       param_list[6][1],
                       param_list[7][1],
                      )

def set_directory(dir_type):
    repeat = True
    print "Input the path where the "+ dir_type + " files are save"
    while repeat:
        dir = raw_input("> ")
        if os.path.exists(dir):
            repeat = False
        else:
            print "The path you typed does not exist. Try again"
    return dir


class PhotoRenamer:
    def __init__(self):
        db_line = []
        # contains
        # src_f : source file
        # tms : source dir
        # dst_f = distination file (saved in a repository directory)
        # dst_d = distination dir
        # tme = timestamp (the datetime when the photo is taken)

    def get_originals(self, dir, ex_list):
        os.chdir(dir)
        originals = []
        for data in os.listdir(dir):
            root, ext = os.path.splitext(data)
            if ext and ext[1:] in ex_list:
                # ext has a commam at the head of it,
                # thus, the commam should be cut off to value
                # if the extension matchs with it in the configuration
                originals.append(data)
        return originals

    def get_db(self, db_file, db_dir):
        os.chdir(db_dir)
        # From here, read CSV file
        # Create list of which the db consist
        # CSV format is below:
        # original_filename, date_taken, original_directory,
        # renamed_name, date_renamed, renamed_directory,
        reader = csv.reader(open(db_file,'r'))
        dbdata = [d for d in reader]
        return dbdata

    def get_original_name_list_in_db(self, dbdata):
        original_name_list = []
        if len(dbdata) and len(dbdata[0]):
            #original_name_list = [d[0] for d in dbdata if len(d)]
            original_name_list = [d[0] for d in dbdata]
        else:
            pass
        return original_name_list

    def get_prefix_dic(self, dbdata):
        prefix_dic = {}
        if len(dbdata) and len(dbdata[0]):
            for data in dbdata:
                p_date = data[1]
                if p_date in prefix_dic.keys():
                    prefix_dic[p_date] = prefix_dic[p_date] + 1
                else:
                    prefix_dic[p_date] = 0
        else:
            pass
        return prefix_dic

    def get_shooting_date(self, src_dir, photo):
        os.chdir(src_dir)
        try:
            image = pyexiv2.Image(photo)
            image.readMetadata()
            photo_date = image['Exif.Photo.DateTimeDigitized']
            shooting_date = photo_date.strftime('%Y%m%d')
            return shooting_date
        except:
            return False

    def copy(self, src_dir, src_name, rep_dir, new_name):
        src = os.path.join(src_dir, src_name)
        dst = os.path.join(rep_dir, new_name)
        try:
            shutil.copyfile(src, dst)
            return True
        except:
            print "Error occured while a file is copied"
            return False

    def write_db(self, db_dir, db_file, dbdata):
        os.chdir(db_dir)
        writer = csv.writer(file(db_file, 'a'))
        try:
            for line in dbdata:
                writer.writerow(line)
        except:
            print "Something wrong while data is written to DB"
            return False
        return True

    def write_error(self, db_dir, err_file, errdata):
        os.chdir(db_dir)
        writer = csv.writer(file(err_file, 'a'))
        try:
            for line in errdata:
                writer.writerow(line)
        except:
            print "Something wrong while error data is writtern"
            return False
        return True

    def start(self, C_conf):
        conf = C_conf
        print "photorenamer has been executed"
        src_list = self.get_originals(conf.source_dir, conf.file_type)
        dbdata = self.get_db(conf.db_file, conf.db_dir)
        renamed_list = self.get_original_name_list_in_db(dbdata)
        prefix_dic = self.get_prefix_dic(dbdata)
        write_data = []
        error_data = []
        for src in src_list:
            os.chdir(conf.source_dir)
            shooting_date = self.get_shooting_date(conf.source_dir, src)
            if shooting_date:
                body, ext = os.path.splitext(src)
                if shooting_date in prefix_dic.keys():
                    prefix_dic[shooting_date] = int(prefix_dic[shooting_date]) + 1
                    seq = prefix_dic[shooting_date]
                else:
                    prefix_dic[shooting_date] = 0
                    seq = prefix_dic[shooting_date]
                new_name = shooting_date + "_" + str(seq) + ext
                self.copy(conf.source_dir, src, conf.repository_dir, new_name)
                current_now = datetime.datetime.today()
                write_now = current_now.strftime('%Y%m%d')
                db_line = [src, shooting_date, conf.source_dir,
                           new_name, write_now, conf.repository_dir]
                write_data.append(db_line)
            else:
                _error = src + " has no Exif.Photo.DateTimeDigitized data"
                print _error
                alert_error = [_error]
                error_data.append(alert_error)
        self.write_db(conf.db_dir, conf.db_file, write_data)
        self.write_error(conf.db_dir, conf.error_file, error_data)


def main():
    work_dir = os.path.abspath(os.path.dirname(__file__))
    os.chdir(work_dir)
    conf = _Configuration()
    if os.path.exists(os.path.join(work_dir, CONF_FILE_NAME)):
        conf.get_param_list(CONF_FILE_NAME, work_dir)
    else:
        source_dir = set_directory(DIR_TYPE['S'])
        repository_dir = set_directory(DIR_TYPE['R'])
        conf.set_param(CONF_FILE_NAME,
                       DB_FILE_NAME,
                       work_dir,
                       source_dir,
                       repository_dir,
                       FILE_TYPE,
                       ERROR_FILE,
                       )
        conf.write_conf()
        conf.init_db()

    photorenamer = PhotoRenamer()
    photorenamer.start(conf)


if __name__ == '__main__':
    main()
