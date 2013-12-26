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
        """ Return character count and line count of the file
             note: for binary files, the int(size) in KiB is returned for both values
             note: the last blank line is ignored (if any), but the \n's are counted

            :type file_obj: inspector.models.base.File
        """
        binary = cls.is_binary(file_obj)
        if binary:
            return file_obj.file_size / 1024, file_obj.file_size / 1024

        loc = file_obj.lines_count

        minified = False
        if file_obj.filename.endswith('.min.js'):
            minified = True
        else:
            for i in range(min(len(file_obj.lines), cls.MIN_MAX_LOC)):
                l = file_obj.lines[i]
                if len(l) > cls.MIN_LINE_LEN_THRESHOLD and l.count(' ') < .10 * len(l):
                    minified = True
                    break

        dumped = False
        if file_obj.filename.endswith('.json') or file_obj.filename.endswith('.sql'):
            dumped = True

        if dumped:
            return file_obj.chars_count / 100, file_obj.chars_count / 100

        if minified:
            return file_obj.chars_count / 10000, file_obj.chars_count / 10000

        return file_obj.chars_count, loc
