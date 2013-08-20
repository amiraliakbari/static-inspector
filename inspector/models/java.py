# -*- coding: utf-8 -*-
import re

from inspector.parser.base import Token, LanguageSpecificParser
from inspector.models.base import (Project, SourceFile, Class, Method, Import, Comment, Statement, ExceptionBlock,
                                   CodeBlock, ForBlock, WhileBlock, IfBlock)
from inspector.models.consts import Language
from inspector.models.exceptions import ParseError
from inspector.utils.lang import enum


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


class JavaSourceFile(SourceFile):
    def __init__(self, filename, package=None):
        self.interfaces = []
        super(JavaSourceFile, self).__init__(filename, package=package)

    def __unicode__(self):
        u = super(JavaSourceFile, self).__unicode__()
        if self.interfaces:
            u += u', {0} interfaces'.format(len(self.interfaces))
        return u

    @property
    def language(self):
        return Language.JAVA

    def next_token(self):
        """
            :return: next token, parsed
            :rtype: Token
        """
        t = Token()
        self.skip_spaces()

        prefix = self.read_ahead(2)  # to detect comments
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

            class IsNotBreaking(object):
                def __init__(self):
                    self.par_open = 0

                def __call__(self, ch):
                    if ch == '(':
                        self.par_open += 1
                    elif ch == ')':
                        self.par_open -= 1
                    else:
                        if not self.par_open and ch in ['{', '}', ';']:
                            return False
                    return True

            l1 = self._cur_line
            t.content = self.read(cond=IsNotBreaking())
            l2 = self._cur_line
            first_head = self.current_head()
            ch = self.next_char()
            if ch == '}':
                if t.content.strip():
                    raise ParseError(u'Unexpected token: } in "{0}".'.format(t.content))
                t.type = 'end-control'
                t.content = '}'

                # context
                try:
                    tmp = self.context_pop()
                    if tmp.isinstance(CodeBlock):
                        tmp.model.ending_line = l2
                except IndexError:
                    raise ParseError(u'Unmatched }.')

            elif ch == '{':
                t.type = 'control'
                t.content = t.content.strip()
                push = False
                repush = False

                # Exception
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
                    # print ">>>", top_if.model, type(top_if.model)
                    if top_if.isinstance(IfBlock):
                        if t.content.startswith('else if'):  # TODO: is this ok for java?
                            top_if.model.add_elif(t.content[7:].strip())  # TODO: remove (), etc.
                            repush = True
                        else:
                            top_if.model.activate_else()
                            repush = True
                    else:
                        else_code = t.content + self.read_ahead(30).replace('\n', '\\n')
                        raise ParseError('else not in a if block: {0}...'.format(else_code))

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

                    # TODO: is it necessary to use parent_block here?
                    parent_class = self.find_context_top(lambda x: x.isinstance(Class))
                    if parent_class:
                        parent_class = parent_class.model

                    if not t.model:
                        t.model = JavaClass.try_parse(t.content, {u'parent_class': parent_class})
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

                        class OpenClassDef(object):
                            def __init__(self):
                                self.par_open = 0

                            def __call__(self, ch):
                                if ch == '{':
                                    self.par_open += 1
                                elif ch == '}':
                                    self.par_open -= 1
                                    if self.par_open == 0:
                                        return False
                                return True

                        current_head = self.current_head()
                        self.rewind_to(first_head)
                        s = self.read(cond=OpenClassDef(), beyond=1)
                        self.skip_spaces()
                        if self.next_char() != ';' or not re.match(r'^.+\s*=\s*new\s+.+\(.*\)$', t.content, re.DOTALL):
                            t.model = None
                            self.rewind_to(current_head)
                        else:
                            t.model = ClassDefiningStatement('%s %s;' % (t.content, s))
                            push = False

                    if not t.model:
                        raise ParseError(u'Token can not be parsed: "{0}".'.format(t.content))

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

                is_special_statement = False

                # package
                PACKAGE_RE = re.compile(r'package\s+([a-zA-Z0-9_.]+)\s*;')
                pm = PACKAGE_RE.match(t.content)
                if pm:
                    self.package = pm.group(1).strip()  # TODO: check with file path
                    is_special_statement = True

                # if without {
                if t.content.startswith('if ') or t.content.startswith('if('):
                    t.model = IfBlock(t.content[3:].strip()[:-1])
                    t.model.starting_line = l1
                    t.model.ending_line = l2
                    t.type = 'control'
                    self._last_popped = t
                else:
                    # normal statement
                    t.model = JavaImport.try_parse(t.content)
                if not t.model:
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

            elif ch is None:
                t = None

            else:
                assert False

        # final cares
        self.skip_spaces()
        if t:
            t.normalize_content()
            if hasattr(t.model, 'source_file'):
                t.model.source_file = self
        return t

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
        if len(self.extends) > 1:
            raise ParseError(u'Multiple inheritance is not supported in Java.')
        self.access = access or self.ACCESS.PACKAGE
        self.implements = implements or []  # TODO: set real Interface reference

    @classmethod
    def parse_access(cls, access_str):
        if not access_str:
            return cls.ACCESS.PACKAGE

        for k, v in cls.ACCESS.display_name.items():
            if v == access_str:
                return k
        return None

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
                         access=JavaClass.parse_access(acc_str.strip() if acc_str else None))


class JavaInterface(JavaClass):
    INTERFACE_RE = re.compile(r'^(\w+\s+)?interface\s*(\w+)(?:\s+implements\s*(.+?)\s*)?$')

    def __init__(self, name, source_file=None, package=None, parent_class=None, access=None, implements=None):
        super(JavaInterface, self).__init__(name, source_file=source_file, package=package, parent_class=parent_class,
                                            access=access, implements=implements)

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
                             access=JavaClass.parse_access(acc_str.strip() if acc_str else None))


class JavaMethod(Method, LanguageSpecificParser):
    # TODO: initial groups may come in other orders
    # TODO: better detection of templates
    METHOD_RE = re.compile(r'^(@[a-zA-Z0-9_]+\s+)?([a-z]+\s+)?(static\s+)?(synchronized\s+)?([a-zA-Z0-9._<>]+\s+)?(\w+)\s*\((.*)\)(?:\s*throws ([a-zA-Z0-9<>_.,]+))?$')

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

        # method name can not be a reserved word
        if method_name in ['synchronized']:
            return None

        m = JavaMethod(parent_class,
                       name=method_name,
                       arguments=[split_arg(s) for s in args_str.split(',')] if args_str else [],
                       return_type=fm.group(5),
                       synchronized=fm.group(4),
                       binding=Method.parse_binding(fm.group(3)),
                       access=Method.parse_access(fm.group(2), default=Method.ACCESS.PACKAGE),
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
