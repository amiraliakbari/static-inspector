# -*- coding: utf-8 -*-
import re
import logging

from inspector.parser.base import Token, LanguageSpecificParser
from inspector.models.base import (Project, SourceFile, Class, Method, Import, Comment, Statement, ExceptionBlock,
                                   CodeBlock, ForBlock, WhileBlock, IfBlock, Field, SwitchBlock, Function)
from inspector.models.consts import Language
from inspector.models.exceptions import ParseError
from inspector.utils.arrays import find
from inspector.utils.lang import enum


logging.basicConfig(filename='logs.log', filemode='w', level=logging.DEBUG)
logger = logging.getLogger('java_parser')


class JavaProject(Project):
    def load_file(self, rel_path):
        """
            :rtype: JavaSourceFile or SourceFile
        """
        # TODO: determine package
        abs_path = self.build_path(rel_path)
        if rel_path.endswith('.java'):
            return JavaSourceFile(abs_path, package=None)
        return SourceFile(abs_path, package=None)


class IsNotBreaking(object):
    """ Used to detect {}; in (), i.e. no-blocking ones
    """

    def __init__(self, breakings=None):
        self.breakings = breakings or ['{', '}', ';']
        self.par_open = 0

    def __call__(self, ch):
        if ch == '(':
            self.par_open += 1
        elif ch == ')':
            self.par_open -= 1
        else:
            if not self.par_open and ch in self.breakings:
                return False
        return True


class IsNotStatementBreaking(object):
    """ Used to detect {}; in (), i.e. no-blocking ones
    """

    def __init__(self, initial_open=0):
        self.par_open = initial_open

    def __call__(self, ch):
        if ch in ['(', '{', '[']:
            self.par_open += 1
        elif ch in [')', '}', ']']:
            self.par_open -= 1
        else:
            if not self.par_open and ch == ';':
                return False
        return True


class JavaSourceFile(SourceFile):
    def __init__(self, filename, package=None):
        self.interfaces = []  # shows Interfaces defined directly in this source file
                              #  this is in addition to self.classes, java specific
        super(JavaSourceFile, self).__init__(filename, package=package)

    def __unicode__(self):
        u = super(JavaSourceFile, self).__unicode__()
        if self.interfaces:
            u += u', {0} interfaces'.format(len(self.interfaces))
        return u

    @property
    def language(self):
        return Language.JAVA

    ##########################
    #  Model Access Helpers  #
    ##########################
    def get_interface(self, name):
        """
            :rtype: JavaInterface
        """
        return find(self.interfaces, lambda m: m.name == name)

    #############
    #  Parsing  #
    #############
    def add_statement(self, t, is_special_statement=False):
        t.type = 'statement'
        t.model = JavaStatement.try_parse(t.content)
        if t.model:
            if not is_special_statement:
                ct = self.find_context_top()
                if ct.isinstance(CodeBlock):
                    ct.model.add_statement(t.model)
                else:
                    raise ParseError(u'Statement is not in a block: {0}.'.format(t.model))
        else:
            raise ParseError(u'Invalid statement: "{0}"'.format(t.content))

    def finalize_token(self, t):
        if t is not None:
            t.normalize_content()
            logger.info('Token: %s', t.model or t.content)
            if hasattr(t.model, 'source_file'):
                t.model.source_file = self
            if self.sw and t.model:
                self.sw.model.add_statement(t.model)
        return t

    def next_token(self):
        t = Token()
        self.skip_spaces()

        # Comments #
        prefix = self.read_ahead(2)
        if prefix == '//':
            t.type = 'comment'
            l1 = self._cur_line
            t.content = self.read(cond=lambda ch: ch != '\n')
            t.model = Comment(t.content)
            t.model.starting_line = l1
            t.model.ending_line = l1
        elif prefix == '/*':
            t.type = 'comment'
            l1 = self._cur_line
            t.content = self.read(find='*/', beyond=2)
            l2 = self._cur_line
            t.model = Comment(t.content)
            t.model.starting_line = l1
            t.model.ending_line = l2

        else:
            # read up to the next blocking {};
            l1 = self._cur_line
            first_head = self.current_head()  # just if needed for rewinding
            t.content = self.read(cond=lambda ch: ch not in ['{', '}', ';'])
            # in case of for declaration, reread to skip ; inside parentheses
            if t.content.startswith('for'):
                self.rewind_to(first_head)
                t.content = self.read(cond=IsNotBreaking())
            # gathering some more data for error reporting, just in case
            l2 = self._cur_line
            logger.debug('='*40)
            logger.debug('CONTENT:'+t.content if t.content is not None else '<NONE>')

            # finding parent blocks #
            # TODO: is it necessary to use parent_*block* here?
            parent_class = self.find_context_top(lambda x: x.isinstance(Class))
            if parent_class:
                parent_class = parent_class.model
            parent_function = self.find_context_top(lambda x: x.isinstance(Function))
            if parent_function:
                parent_function = parent_function.model
            parent_block = self.find_context_top(lambda x: x.isinstance(CodeBlock))
            if parent_block:
                parent_block = parent_block.model
            self.sw = self.find_context_top(lambda x: x.isinstance(SwitchBlock))

            ch = self.next_char()
            if self.sw:
                logger.debug('IN a switch: %s', self.sw)
                m1 = re.match(r'^case\s+(?P<cond>.+?)\s*:', t.content)
                m2 = re.match(r'^default\s*:', t.content)
                if m1 or m2:
                    ch = ';'  # it is a goto! i.e. goto Switch Case handling code

            # End-Control Token #
            if ch == '}':
                if t.content.strip():
                    raise ParseError(u'Unexpected token: }} in "{0}".'.format(t.content))
                t.type = 'end-control'
                t.content = '}'

                # context
                try:
                    tmp = self.context_pop()

                    if tmp.isinstance(SwitchBlock):
                        self.sw = tmp.model
                        # print '(((((((((((((((('
                        # print sw.condition
                        # for k in sw.case_orders:
                        #     print 'CASE', k, ':', sw.cases[k]
                        # print 'DEFAULT:', sw.default
                        # print ')))))))))))))))))'

                    if tmp.isinstance(CodeBlock):
                        tmp.model.ending_line = l2
                except IndexError:
                    raise ParseError(u'Unmatched }.')

            # Control Token #
            elif ch == '{':
                t.type = 'control'
                t.content = t.content.strip()
                push = False
                repush = False

                if t.content == 'try':
                    t.model = ExceptionBlock()
                    push = True
                elif t.content.startswith('catch'):
                    top_try = self._last_popped
                    if top_try.isinstance(ExceptionBlock):
                        top_try.model.add_catch(t.content[5:].strip())  # TODO: remove (), etc.
                        repush = True
                    else:
                        raise ParseError(u'catch not in a try block: {0}.'.format(t.content))

                # IfBlock
                elif t.content.startswith('if ') or t.content.startswith('if('):
                    t.model = IfBlock(t.content[3:].strip()[:-1])
                    push = True
                elif t.content.startswith('else'):
                    top_if = self._last_popped
                    # for x in self._context:
                    #     print type(x.model).__name__, x.model
                    # print "---", top_if.model, type(top_if.model)
                    if top_if.isinstance(IfBlock):
                        t.model = top_if.model
                        if t.content.startswith('else if'):  # TODO: is this ok for java?
                            top_if.model.add_elif(t.content[7:].strip())  # TODO: remove (), etc.
                            repush = True
                        else:
                            top_if.model.activate_else()
                            repush = True
                    else:
                        else_code = t.content + self.read_ahead(30).replace('\n', '\\n')
                        raise ParseError('else not in a if block: {0}...'.format(else_code))

                # SwitchBlock
                elif t.content.startswith('switch(') or t.content.startswith('switch '):
                    t.model = SwitchBlock(t.content[7:].strip()[:-1])
                    push = True

                # ForBlock
                elif t.content.startswith('for'):
                    t.model = ForBlock()
                    push = True

                # WhileBlock
                elif t.content.startswith('while'):
                    t.model = WhileBlock()
                    push = True

                # More complex parts (class, method)
                else:
                    push = True

                    if not t.model:
                        t.model = JavaClass.try_parse(t.content, {u'parent_class': parent_class})
                    if not t.model:
                        t.model = JavaAnonymousClass.try_parse(t.content, {u'parent_class': parent_class})
                        if t.model:
                            parent_function.nested_classes.append(t.model)
                            # adding the containing statement
                            ch = self.current_head()
                            st_content = t.content + ' { ' + self.read(cond=IsNotStatementBreaking(initial_open=1))
                            tt = Token(content=st_content)
                            self.add_statement(tt)
                            self.finalize_token(tt)
                            # marking the statement as pre-read
                            self.statement_pre_read = self.current_head()
                            # back to the start of the AnonymousClass
                            self.rewind_to(ch)
                    if not t.model:
                        t.model = JavaSynchronizedBlock.try_parse(t.content)
                        if t.model:
                            top = self.find_context_top(lambda x: x.isinstance(CodeBlock))
                            top.model.add_statement(t.model)  # TODO: this makes problems! (because of type)
                    if not t.model:
                        t.model = JavaInterface.try_parse(t.content, {u'parent_class': parent_class})
                    if not t.model:
                        t.model = JavaMethod.try_parse(t.content, {u'parent_class': parent_class})

                    if not t.model:
                        raise ParseError(u'Token can not be parsed: "{0}".'.format(t.content))
                # Exception

                if repush:
                    self._context.append(self._last_popped)
                elif push:
                    # print "pushing", t.model
                    if t.isinstance(CodeBlock):
                        t.model.starting_line = l1
                    self._context.append(t)

            elif ch == ';':
                t.type = 'statement'
                t.content += ';'

                if self.statement_pre_read is not None:
                    current_head = self.current_head()
                    if current_head > self.statement_pre_read + 1:
                        raise AssertionError('bad pre-read! pre-read: {0}, current: {1}'.format(self.statement_pre_read,
                                                                                                current_head))
                    else:
                        logger.info('Statement already read, skipping: %s', t.content)
                        if self.statement_pre_read == current_head - 1:
                            self.statement_pre_read = None
                else:
                    is_special_statement = False

                    PACKAGE_RE = re.compile(r'package\s+([a-zA-Z0-9_.]+)\s*;')
                    pm = PACKAGE_RE.match(t.content)

                    # case
                    if self.sw:
                        logger.debug("IN SWITCH: %s", t.content)

                        m = re.match(r'^case\s+(?P<cond>.+?)\s*:', t.content)
                        if m:
                            logger.debug('OPENDED case: %s', m.group('cond'))
                            self.sw.model.add_case(m.group('cond'))
                            logger.debug('SWITCH is: %s', self.sw)
                            t = None

                        elif re.match(r'^default\s*:', t.content):
                            logger.debug('SWITCH default')
                            self.sw.model.add_default()
                            logger.debug('SWITCH is: %s', self.sw)
                            t = None

                        if t is None:
                            self.rewind_to(first_head)
                            self.read(find=':', beyond=1)

                    # package
                    elif pm:
                        self.package = pm.group(1).strip()  # TODO: check with file path
                        is_special_statement = True

                    # if without {
                    elif t.content.startswith('if ') or t.content.startswith('if('):
                        t.model = IfBlock(t.content[3:].strip()[:-1])
                        t.model.starting_line = l1
                        t.model.ending_line = l2
                        t.type = 'control'
                        self._last_popped = t

                    # class field
                    elif not t.model and parent_class:
                        if parent_block == parent_class:
                            # fields must be defined directly in classes
                            t.model = JavaField.try_parse(t.content, {u'parent_class': parent_class})
                            if t.model:
                                if isinstance(t.model, list):
                                    for f in t.model:
                                        parent_class.add_statement(f)
                                    t.model = t.model[0]
                                else:
                                    parent_class.add_statement(t.model)

                    # import
                    if t and not t.model:
                        t.model = JavaImport.try_parse(t.content)

                    # normal statement
                    if t and not t.model:
                        self.add_statement(t, is_special_statement)

                    if t and not t.model:
                        logger.error("Can not parse: %s", t.content)

            elif ch is None:
                t = None

            else:
                assert False

        # final cares
        self.skip_spaces()
        return self.finalize_token(t)

    def _save_model(self, token_model):
        if isinstance(token_model, JavaInterface):
            self.interfaces.append(token_model)
        else:
            super(JavaSourceFile, self)._save_model(token_model)


class JavaClass(Class, LanguageSpecificParser):
    # TODO: better detection of templates
    CLASS_RE = re.compile(r'^(\w+\s+)?class\s*(\w+)(?:\s*extends\s*([a-zA-Z0-9_.<>]+))?(?:\s+implements\s*(.+?)\s*)?$')
    ACCESS = enum('UNKNOWN', 'PRIVATE', 'PROTECTED', 'PACKAGE', 'PUBLIC',
                  verbose_names=['unknown', 'private', 'protected', 'package', 'public'])

    def __init__(self, name, source_file=None, package=None, parent_class=None, extends=None, access=None,
                 implements=None):
        super(JavaClass, self).__init__(name, source_file=source_file, package=package, parent_class=parent_class,
                                        extends=extends)
        # TODO: should we set package from "package ...;" line or from source file?
        if len(self.extends) > 1:
            raise ParseError(u'Multiple inheritance is not supported in Java.')
        if isinstance(access, str) or isinstance(access, unicode):
            access = JavaClass.parse_access(access)
        self.access = access or self.ACCESS.PACKAGE
        self.implements = implements or []  # TODO: set real Interface reference

    @property
    def qualified_name(self):
        qn = super(JavaClass, self).qualified_name
        p = qn.split('.')
        if len(p) > 1 and p[-1] == p[-2]:
            p = p[:-1]
        return '.'.join(p)

    @classmethod
    def parse_access(cls, access_str):
        """
            :type access_str: str or unicode or None
        """
        if access_str:
            access_str = access_str.strip()
        if not access_str:
            return cls.ACCESS.PACKAGE

        for k, v in cls.ACCESS.display_name.items():
            if v == access_str:
                return k
        return cls.ACCESS.UNKNOWN

    @classmethod
    def try_parse(cls, string, opts=None):
        opts = opts or {}
        cm = cls.CLASS_RE.match(string)
        if not cm:
            return None

        acc_str = cm.group(1)
        ext_str = cm.group(3)
        imp_str = cm.group(4)
        return JavaClass(name=cm.group(2),
                         parent_class=opts.get(u'parent_class'),
                         extends=ext_str,
                         implements=[s.strip() for s in imp_str.split(',')] if imp_str else [],
                         access=acc_str)


class JavaAnonymousClass(JavaClass):
    PATTERN = re.compile(r'^(?P<lead>(.*?)[= (,])?new\s+(?P<type>[a-zA-Z0-9._<>]+)\s*\((?P<constructor_params>.*?)\)$', re.DOTALL)

    def __init__(self, name, constructor_parameters=None, **kwargs):
        kwargs['access'] = 'PRIVATE'  # we assume that anonymous classes access is PRIVATE
        super(JavaAnonymousClass, self).__init__(name, **kwargs)
        self.constructor_parameters = constructor_parameters or []

    @classmethod
    def try_parse(cls, string, opts=None):
        opts = opts or {}
        cm = cls.PATTERN.match(string)
        if not cm:
            return None

        parent_type_str = cm.group('type')
        params_str = cm.group('constructor_params')
        params_strs = params_str.split(',') if params_str else []
        return cls(name='',
                   constructor_parameters=[p.strip() for p in params_strs],
                   parent_class=opts.get(u'parent_class'),
                   extends=parent_type_str,  # TODO: detect this is parent class or interface, currently just class
                   )


class JavaInterface(JavaClass):
    INTERFACE_RE = re.compile(r'^(\w+\s+)?interface\s*(\w+)(?:\s+implements\s*(.+?)\s*)?$')

    def __init__(self, name, source_file=None, package=None, parent_class=None, access=None, implements=None):
        super(JavaInterface, self).__init__(name, source_file=source_file, package=package, parent_class=parent_class,
                                            access=access, implements=implements)
        self.abstract_methods = []

    #############
    #  Parsing  #
    #############
    def add_statement(self, statement):
        if isinstance(statement, Statement):
            code = statement.code.strip()
            if code.endswith(';'):
                logger.warning('Try interface: `%s`', code)
                m = JavaMethod.try_parse(code[:-1], {'parent_class': self})
                if m:
                    self.abstract_methods.append(m)
                    return
        return super(JavaInterface, self).add_statement(statement)

    @classmethod
    def try_parse(cls, string, opts=None):
        opts = opts or {}
        cm = cls.INTERFACE_RE.match(string)
        if not cm:
            return None

        acc_str = cm.group(1)
        imp_str = cm.group(3)
        return JavaInterface(name=cm.group(2),
                             parent_class=opts.get(u'parent_class'),
                             implements=[s.strip() for s in imp_str.split(',')] if imp_str else [],
                             access=acc_str)


class JavaField(Field, LanguageSpecificParser):
    MATCH_RE = re.compile(r'^(@\w+\s+)?(\w+\s+)?(static\s+)?([a-zA-Z0-9<>\[\].j_]+)\s+(.*?)\s*;$', re.DOTALL)

    @classmethod
    def try_parse(cls, string, opts=None):
        opts = opts or {}
        cm = cls.MATCH_RE.match(string)
        # print "+", cm.groups() if cm else ""
        if not cm:
            return None

        an = cm.group(1)
        vs = JavaClass.parse_access(cm.group(2))
        tp = cm.group(4)
        name = cm.group(5)

        results = []

        names = []
        last_i = 0
        open_chs = ['()', '[]', '{}']
        open_cnt = [0] * len(open_chs)
        for i, c in enumerate(name):
            for j, op in enumerate(open_chs):
                if c == op[0]:
                    open_cnt[j] += 1
                elif c == op[1]:
                    open_cnt[j] -= 1
            if c == ',':
                if open_cnt == [0] * len(open_cnt):
                    names.append(name[last_i:i].strip())
                    last_i = i + 1
        if last_i < len(name):
            names.append(name[last_i:].strip())

        for n in names:
            # print "++", n
            m = re.match(r'^(\w+)(\s*=.+)?$', n.strip(), re.DOTALL)
            # print "+++", m
            if m:
                results.append(Field(m.group(1), tp, initializer=m.group(2), is_static=cm.group(3) is not None,
                                     parent_class=opts.get(u'parent_class'), visibility=vs, annotations=an))
            else:
                return None
        if not results:
            return None
        if len(results) == 1:
            results = results[0]
        return results


class JavaMethod(Method, LanguageSpecificParser):
    # TODO: initial groups may come in other orders
    # TODO: better detection of templates
    METHOD_RE = re.compile(r'^(@[a-zA-Z0-9_]+\s+)?([a-z]+\s+)?(static\s+)?(synchronized\s+)?([a-zA-Z0-9._<>]+\s+)?(\w+)\s*\((.*?)\)(?:\s*throws ([a-zA-Z0-9<>_.,]+))?$',
                           re.DOTALL)

    def __init__(self, *args, **kwargs):
        self.synchronized = kwargs.pop(u'synchronized', None) or False
        self.annotations = []
        super(JavaMethod, self).__init__(*args, **kwargs)

    @classmethod
    def try_parse(cls, string, opts=None):
        opts = opts or {}
        fm = cls.METHOD_RE.match(string)
        if not fm:
            return None

        parent_class = opts.get(u'parent_class')
        if parent_class is None:
            raise ParseError(u'Functions must be in a class in Java.')

        def split_arg(s):
            si = s.strip().rfind(' ')
            if si == -1:
                return '?', s
            return s[:si], s[si + 1:]

        method_name = fm.group(6)
        throw_str = fm.group(8)
        args_str = fm.group(7)

        acc_str = fm.group(2)
        ret_str = fm.group(5)
        if acc_str:
            acc_str = acc_str.strip()
        if ret_str:
            ret_str = ret_str.strip()
        if not Method.parse_access(acc_str):
            ret_str, acc_str = acc_str, ret_str

        # method name can not be a reserved word
        if method_name in ['synchronized', 'switch']:
            return None

        m = JavaMethod(parent_class,
                       name=method_name,
                       arguments=[split_arg(s) for s in args_str.split(',')] if args_str else [],
                       return_type=ret_str,
                       synchronized=fm.group(4),
                       binding=Method.parse_binding(fm.group(3)),
                       access=Method.parse_access(acc_str, default=Method.ACCESS.PACKAGE),
                       throws=[s.strip() for s in throw_str.split(',')] if throw_str else None)

        annotations = fm.group(1)
        if annotations:
            m.annotations.append(annotations)

        return m


class JavaImport(Import, LanguageSpecificParser):
    """ Specific Model for Java imports

        see:
          * static import: http://docs.oracle.com/javase/1.5.0/docs/guide/language/static-import.html
    """
    IMPORT_RE = re.compile(r'^import\s+(static\s+)?([a-zA-Z0-9._*]+)\s*;$')

    def __init__(self, *args, **kwargs):
        self.is_static = kwargs.pop('is_static', False)
        super(JavaImport, self).__init__(*args, **kwargs)

    @property
    def imported_identifier(self):
        iden = self.import_str.split('.')[-1]
        if iden == '*':
            # TODO: what to do here?
            pass
        return iden

    @classmethod
    def try_parse(cls, string, opts=None):
        """
            :param str or unicode string: code to be parsed
            :rtype: Import
        """
        im = cls.IMPORT_RE.match(string)
        if im:
            is_static = im.group(1) == 'static'
            import_str = im.group(2)
            return JavaImport(import_str, is_static=is_static)
        return None


class JavaStatement(Statement, LanguageSpecificParser):
    @classmethod
    def try_parse(cls, string, opts=None):
        """
            :param str or unicode string: code to be parsed
            :rtype: Statement
        """
        # TODO: any checks required?
        return Statement(string)


class ClassDefiningStatement(JavaStatement):
    @classmethod
    def try_parse(cls, string, opts=None):
        """
            :param str or unicode string: code to be parsed
            :rtype: Statement
        """
        # TODO: any checks required?
        return Statement(string)


class JavaSynchronizedBlock(CodeBlock, LanguageSpecificParser):
    SYNC_BLOCK_RE = re.compile(r'^synchronized\s*(\((?:\s|\w|[,.])+\))?\s*$')

    def __init__(self, locked_values=None):
        super(JavaSynchronizedBlock, self).__init__()
        self.locked_values = locked_values

    @classmethod
    def try_parse(cls, string, opts=None):
        """
            :param str or unicode string: code to be parsed
            :rtype: Statement
        """
        sb = cls.SYNC_BLOCK_RE.match(string)
        if sb:
            return JavaSynchronizedBlock(locked_values=sb.group(1))
        return None
