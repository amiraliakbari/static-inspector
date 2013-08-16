# -*- coding: utf-8 -*-


class FileAnalyzer(object):
    MIN_LINE_LEN_THRESHOLD = 300
    MIN_MAX_LOC = 20

    @classmethod
    def is_binary(cls, file_obj):
        """
            :type file_obj: inspector.models.base.File
        """
        textchars = ''.join(map(chr, [7, 8, 9, 10, 12, 13, 27] + range(0x20, 0x100)))
        with open(file_obj.get_abs_path(), 'r') as f:
            sample_bytes = f.read(1024)
        return bool(sample_bytes.translate(None, textchars))

    @classmethod
    def estimate_file_size(cls, file_obj):
        """
            :type file_obj: inspector.models.base.File
        """
        binary = cls.is_binary(file_obj)
        if binary:
            return file_obj.file_size / 1024

        loc = file_obj.lines_count
        if loc < cls.MIN_MAX_LOC:
            minified = False
            for l in file_obj.lines:
                if len(l) > cls.MIN_LINE_LEN_THRESHOLD:
                    minified = True
                    break
            if minified:
                return file_obj.chars_count / 1000
        return loc
