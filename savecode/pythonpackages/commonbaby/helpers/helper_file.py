"""help for file operation"""

# -*- coding:utf-8 -*-

import os
import tarfile
import threading
import time
import datetime
import uuid


def get_unique_filename_uuid1(dir: str, fileext: str)->str:
    """Generate a unique file name in specified dir. return the file path"""
    if not isinstance(dir, str) or dir == "":
        raise Exception("Specified dir is None")
    if not isinstance(fileext, str) or fileext is None:
        fileext = ""

    fipath = None
    if fileext == "":
        fipath = os.path.join(dir, "%s" % str(uuid.uuid1()))
    else:
        fipath = os.path.join(dir, "%s.%s" %
                              (str(uuid.uuid1()), fileext.strip('.')))

    while os.path.exists(fipath):
        if fileext == "":
            fipath = os.path.join(dir, "%s" % str(uuid.uuid1()))
        else:
            fipath = os.path.join(dir, "%s.%s" %
                                  (str(uuid.uuid1()), fileext.strip('.')))

    return fipath


def rename_file_by_number_tail(srcFi) -> str:
    """
    rename a file by adding numeric flag tail after srcFi filename\n
    srcFi:the source filename, can be full path or only the filename\n
    return:the new full filepath or filename. return empty str if srcFi is None or empty\n
    Example: srcFi='/user/file.ext' -> newFi='user/file0.ext', if file0.exe is
    already exists, then file1.ext"""
    if not isinstance(srcFi, str) or srcFi == "":
        return ''
    dir, finame = os.path.split(srcFi)
    if finame is None or finame == '':
        return ''
    shortname, ext = os.path.splitext(finame)
    if shortname is None or shortname == '':
        return ''
    numflag = 0
    newFi = os.path.join(dir, "%s%d%s" % (shortname, numflag, ext))
    while os.path.exists(newFi) and os.path.isfile(newFi):
        numflag += 1
        newFi = os.path.join(dir, "%s%d%s" % (shortname, numflag, ext))
    return newFi


def targz_compress(target: str,
                   outtar: str = None,
                   replace: bool = True,
                   recursive: bool = True,
                   exclude=None,
                   filter=None):
    """compress the target(folder or a file) to a .tar.gz file.
    [target]: the target file or directory.
    [outtar]: the output tar.gz file path, default is $target.tar.gz.
    [replace]: whether to replace it if the output tar.gz file is exists.
    [recursive]: Directories are added recursively by default. This can be \
        avoided by settingrecursive' to False.
    [exclude]: a function that should return True for each filename to be \
        excluded.
    [filter]: a function that expects a TarInfo object argument and returns \
        the changed TarInfo object, if it returns None the TarInfo object \
        will be excluded from the archive."""
    try:
        if os.path.exists(outtar) and os.path.isfile(outtar):
            if not replace:
                raise FileExistsError(
                    "tar.gz file already exists: %s" % outtar)
            else:
                os.remove(outtar)

        # Mode	    Action
        # 'r|*'	    Open a stream of tar blocks for reading with transparent compression.
        # 'r|'	    Open a stream of uncompressed tar blocks for reading.
        # 'r|gz'	Open a gzip compressed stream for reading.
        # 'r|bz2'	Open a bzip2 compressed stream for reading.
        # 'r|xz'	Open an lzma compressed stream for reading.
        # 'w|'	    Open an uncompressed stream for writing.
        # 'w|gz'	Open a gzip compressed stream for writing.
        # 'w|bz2'	Open a bzip2 compressed stream for writing.
        # 'w|xz'	Open an lzma compressed stream for writing.
        t = tarfile.open(outtar, "w:gz")
        #t.add(target, os.path.split(target)[1], recursive, exclude, filter)
        t.add(
            name=target,
            arcname=os.path.split(target)[1],
            recursive=recursive,
            exclude=exclude,
            filter=filter)
    except Exception as ex:
        pass
    finally:
        t.close()


def get_filePath_recursively(folder: str):
    """get all the file paths recursively"""
    if not os.path.exists(folder):
        return
    if os.path.isfile(folder):
        yield folder
    for root, di, files in os.walk(folder):
        for fi in files:
            fullpath = os.path.join(root, fi)
            yield fullpath


def directory_file_reduce(di: str, keepcount: int = 1000, keepdays: float = 3, on_error: callable = None)->threading.Thread:
    """删除指定目录下的文件，保留指定个数，和指定天数内的文件，返回一个threading.Thread对象，要自己启动这个Thread。\n
    di: 监控的根目录。\n
    keepcount: 保留个数，范围0~65535，为0表示全删，为负数表示全部保留。\n
    keepdays: 保留最后修改日期为n天内的文件，范围0~65535，为0表示全删，为负数表示全部保留。\n
    on_error: 一个函数，此函数接收一个Exception对象，用作当发生错误时的回调"""
    res: threading.Thread = None
    if not isinstance(di, str) or di == "":
        raise Exception("Directory path is empty.")
    di = os.path.abspath(di)
    if not isinstance(keepcount, int):
        raise Exception(
            "Param 'keepcount' is invalid: %s, it must be an integer" % keepcount)
    if not type(keepdays) in [int, float]:
        raise Exception(
            "Param 'keepdays' is invalid: %s, it must be an integer or float" % keepdays)
    res = threading.Thread(target=__directory_file_reduce,
                           kwargs={"di": di, "keepcount": keepcount,
                                   "keepdays": keepdays},
                           daemon=True)
    return res


def __directory_file_reduce(di: str, keepcount: int = 1000, keepdays: int = 3, on_error: callable = None):
    """文件reduce线程"""
    curr_dir_total_cnt: int = 0
    curr_delete_cnt: int = 0
    sort_file_by_time: dict = {}
    seconds = keepdays*24*60*60
    while True:
        try:
            if not os.path.exists(di) or not os.path.isdir(di):
                continue

            curr_dir_total_cnt = 0
            curr_delete_cnt = 0
            for fipath in get_filePath_recursively(di):
                if not isinstance(fipath, str) or not os.path.exists(fipath) or not os.path.isfile(fipath):
                    continue

                curr_dir_total_cnt += 1

                # 如果文件创建时间太早，删除
                fimtime = os.path.getmtime(fipath)
                # 小于0表示全部保留
                if keepdays < 0:
                    pass
                # 等于0表示全部删除
                elif keepdays == 0:
                    os.remove(fipath)
                    curr_delete_cnt += 1
                # 根据文件修改时间判断要不要删
                elif keepdays > 0 and time.time()-fimtime >= seconds:
                    os.remove(fipath)
                    curr_delete_cnt += 1
                # 否则添加到根据时间排序的文件队列
                else:
                    # 小于0表示全部保留
                    if keepcount < 0:
                        pass
                    # 等于0表示全部删除
                    if keepcount == 0:
                        os.remove(fipath)
                        curr_delete_cnt += 1
                    # 否则判断当前文件夹内文件是否超限，若超限，按文件修改时间先后顺序删除
                    else:
                        sort_file_by_time[fipath] = fimtime
                        # 如果文件超限，则按时间先后顺序，先删列表中最早的文件
                        if keepcount > 0 and len(sort_file_by_time) > keepcount:
                            sortdict = list(
                                sorted(sort_file_by_time.items(), key=lambda d: d[1]))
                            fi = sortdict[0][0]
                            if os.path.exists(fi):
                                os.remove(fi)
                            if sort_file_by_time.__contains__(fi):
                                sort_file_by_time.pop(fi)

        except Exception as ex:
            if not on_error is None and callable(on_error):
                on_error(ex)
        finally:
            time.sleep(1)


if __name__ == '__main__':

    di = r"F:\TestFolder\idown\aaa"
    t = directory_file_reduce(di, 5, 2)
    t.start()

    while True:
        time.sleep(1)

    fi = get_unique_filename_uuid1("./aaa", 'ii')

    target = r"F:\TestFolder\testpytar"
    outfi = r"F:\TestFolder\testpytar.tar.gz"
    targz_compress(target, outfi)
