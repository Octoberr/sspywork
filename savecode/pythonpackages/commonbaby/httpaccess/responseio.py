"""request.Response.iter_content() as a 
readable io.BytesIO"""

# -*- coding:utf-8 -*-

import io
import queue
import threading
from functools import wraps

from requests import Response


def raise_closed(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.closed:
            raise Exception("Stream is closed")
        return func(self, *args, **kwargs)

    return wrapper


class ResponseIO(io.RawIOBase):
    """Represents a network response stream"""
    def __init__(self, resp: Response):
        super(ResponseIO, self).__init__()
        if not isinstance(resp, Response):
            raise Exception(
                "param 'iter_bytes_blocks' must be Iterable return btyes blocks"
            )

        self._net_resp: Response = resp
        self.__contents: iter = None
        self.__contents_locker = threading.Lock()
        self.__position: int = 0  #当前流位置，已读取字节数
        self.__last_read_buf_rest_queue: queue.Queue = queue.Queue()

        self.__closed: bool = False
        self.__close_locker = threading.Lock()

        resp.headers.__contains__('content-length')

    def __len__(self):
        if self._net_resp.headers.__contains__('content-length'):
            return int(self._net_resp.headers['content-length'])
        else:
            raise Exception("Invalid operation, cannot get stream length")

    @raise_closed
    def isatty(self):
        return False

    @raise_closed
    def seekable(self):
        return False

    @raise_closed
    def seek(self):
        raise Exception("ResponseIO not supports seek")

    @raise_closed
    def writable(self):
        return False

    @raise_closed
    def write(self):
        raise Exception("ResponseIO not supports write")

    @raise_closed
    def truncate(self, size=None):
        raise Exception("ResponseIO not supports truncate")

    @raise_closed
    def tell(self):
        return self.__position

    @raise_closed
    def readable(self) -> bool:
        return True

    @raise_closed
    def readline(self):
        raise NotImplementedError()

    @raise_closed
    def readlines(self):
        raise NotImplementedError()

    @raise_closed
    def read_block(self,
                   read_buffer_size: int = 1024 * 1024,
                   decode_unicode: bool = False) -> iter:
        """read data blocks, return iterable with byts yield."""
        if self._net_resp is None:
            return
        if not isinstance(read_buffer_size, int) or read_buffer_size < 1:
            raise Exception("param 'read_buffer_size' must be an integer > 0")
        try:
            if self.__contents is None:
                with self.__contents_locker:
                    if self.__contents is None:
                        self.__contents = self._net_resp.iter_content(
                            read_buffer_size, decode_unicode)
        except Exception as ex:
            raise Exception("iter_content of Response error: {}".format(ex))
        for block in self.__contents:
            self.__position += len(block)
            yield block

    @raise_closed
    def read(self,
             size: int = None,
             read_buffer_size: int = 1024 * 1024,
             decode_unicode: bool = False) -> bytes:
        """read at most 'size' data bytes and return"""
        res: bytes = None
        res_len: int = 0

        if size == 0:
            return res

        while True:
            try:
                if not self.__last_read_buf_rest_queue.empty():
                    try:

                        block = self.__last_read_buf_rest_queue.get(
                            timeout=0.001)
                        res, res_len = self.__append_block(
                            res, res_len, block, size)
                        if isinstance(size,
                                      int) and size > 0 and res_len >= size:
                            break
                    finally:
                        self.__last_read_buf_rest_queue.task_done()
                else:
                    break
            except queue.Empty:
                break

        if isinstance(size, int) and size > 0 and res_len >= size:
            return res

        for block in self.read_block(read_buffer_size=read_buffer_size,
                                     decode_unicode=decode_unicode):
            res, res_len = self.__append_block(res, res_len, block, size)
            if isinstance(size, int) and size > 0 and res_len >= size:
                break

        return res

    @raise_closed
    def __append_block(self, res: bytes, res_len: int, block: bytes,
                       size: int) -> (bytes, int):
        """append block to res, at most size bytes."""
        if res is None:
            res = bytes()
        if not size is None and size > 0:
            if res_len >= size:
                if isinstance(block, bytes) and len(block) > 0:
                    self.__last_read_buf_rest_queue.put(block)
                return (res, res_len)
            elif res_len + len(block) >= size:
                append_len = size - res_len
                res += block[:append_len]
                self.__last_read_buf_rest_queue.put(block[append_len + 1:])
                res_len += append_len
                return (res, res_len)
            else:
                res += block
                res_len += len(block)
        else:
            res += block
            res_len += len(block)

        return (res, res_len)

    @raise_closed
    def readinto(self,
                 target_stream: io.BufferedIOBase,
                 read_buffer_size: int = 1024 * 1024,
                 decode_unicode: bool = False):
        """copy bytes from the ResponseIO to target stream.
        Useage: \n
        ha = HttpAccess()\n
        respio = ha.get_response_stream(\n
            'https://www.google.com',\n
            headers='''\n
            accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8\n
            accept-encoding:gzip, deflate, br\n
            accept-language:,zh-CN,zh;q=0.9\n
            ''')\n        
        with open('filepath', mode='wb') as fs:\n
            respio.readinto(fs)\n
        """
        if not isinstance(target_stream, io.IOBase):
            raise Exception("target stream is not a io object")
        if not target_stream.writable():
            raise Exception("target stream is not writable")
        for bs in self.read_block(read_buffer_size=read_buffer_size,
                                  decode_unicode=decode_unicode):
            target_stream.write(bs)

    def close(self):
        """close ResponseIO stream"""
        if self.__closed:
            return
        with self.__close_locker:
            if self.__closed:
                return
            try:

                super(ResponseIO, self).close()

                if not self.__contents is None:
                    self.__contents.close()

                if not self._net_resp is None:
                    self._net_resp.close()

                if not self.__last_read_buf_rest_queue is None:
                    self.__last_read_buf_rest_queue = None

            except Exception:
                pass

            self.__closed = True

    def _checkClosed(self) -> bool:
        return self.__closed

    @raise_closed
    def _checkReadable(self) -> bool:
        return self.readable()

    @raise_closed
    def _checkSeekable(self) -> bool:
        return self.seekable()

    @raise_closed
    def _checkWritable(self) -> bool:
        return self.writable()
