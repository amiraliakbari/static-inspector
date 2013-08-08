# -*- coding: utf-8 -*-


def enum(*sequential, **named):
    verbose_names = named.pop('verbose_names', {})
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.iteritems())
    if isinstance(verbose_names, list):
        verbose_names = dict((i, val) for i, val in enumerate(verbose_names))
    display = verbose_names if verbose_names else reverse
    enums['reverse'] = reverse
    enums['display_name'] = display
    return type('Enum', (), enums)
